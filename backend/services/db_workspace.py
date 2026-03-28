import csv
import io
import re
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import quote_plus
from uuid import uuid4

from sqlalchemy import MetaData, Table, create_engine, inspect, text

from data.models import DatabaseConnectionProfile, session_scope
from services.secret_manager import decrypt_secret, encrypt_secret

try:
    from sshtunnel import SSHTunnelForwarder
except ImportError:  # pragma: no cover
    SSHTunnelForwarder = None


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def now_utc():
    return datetime.utcnow()


def _validate_identifier(value: str, label: str) -> str:
    if not value or not IDENTIFIER_PATTERN.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def generate_profile_id():
    return f"profile-{uuid4().hex[:8]}"


def serialize_profile(profile: DatabaseConnectionProfile) -> dict:
    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "db_type": profile.db_type,
        "host": profile.host,
        "port": profile.port,
        "username": profile.username,
        "default_database": profile.default_database,
        "ssh_enabled": profile.ssh_enabled,
        "ssh_host": profile.ssh_host,
        "ssh_port": profile.ssh_port,
        "ssh_username": profile.ssh_username,
        "ssh_pkey_path": profile.ssh_pkey_path,
        "created_at": profile.created_at.isoformat(timespec="seconds") + "Z" if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat(timespec="seconds") + "Z" if profile.updated_at else None,
    }


def create_profile(payload: dict) -> dict:
    now = now_utc()
    profile_id = generate_profile_id()
    with session_scope() as session:
        profile = DatabaseConnectionProfile(
            profile_id=profile_id,
            name=payload.get("name") or "MySQL Workspace",
            db_type=(payload.get("db_type") or "mysql").lower(),
            host=payload.get("host") or "127.0.0.1",
            port=int(payload.get("port") or 3306),
            username=payload.get("username") or "root",
            password=encrypt_secret(payload.get("password"), persist=bool(payload.get("save_password", True))),
            default_database=payload.get("default_database"),
            ssh_enabled=bool(payload.get("ssh_enabled")),
            ssh_host=payload.get("ssh_host"),
            ssh_port=int(payload.get("ssh_port") or 22) if payload.get("ssh_port") else None,
            ssh_username=payload.get("ssh_username"),
            ssh_password=encrypt_secret(payload.get("ssh_password"), persist=bool(payload.get("save_password", True))),
            ssh_pkey_path=payload.get("ssh_pkey_path"),
            ssh_pkey_passphrase=encrypt_secret(
                payload.get("ssh_pkey_passphrase"),
                persist=bool(payload.get("save_password", True)),
            ),
            created_at=now,
            updated_at=now,
        )
        session.add(profile)
    return get_profile(profile_id)


def list_profiles() -> list[dict]:
    with session_scope() as session:
        items = session.query(DatabaseConnectionProfile).order_by(DatabaseConnectionProfile.created_at.desc()).all()
        return [serialize_profile(item) for item in items]


def get_profile(profile_id: str) -> dict | None:
    with session_scope() as session:
        profile = session.get(DatabaseConnectionProfile, profile_id)
        if profile is None:
            return None
        return serialize_profile(profile)


def get_profile_record(profile_id: str) -> DatabaseConnectionProfile | None:
    with session_scope() as session:
        profile = session.get(DatabaseConnectionProfile, profile_id)
        if profile is None:
            return None
        session.expunge(profile)
        return profile


def _build_mysql_url(profile: DatabaseConnectionProfile, *, database: str | None = None, host: str | None = None, port: int | None = None) -> str:
    target_database = database if database is not None else (profile.default_database or "")
    auth_user = quote_plus(profile.username or "root")
    decrypted_password = decrypt_secret(profile.password) or ""
    auth_password = quote_plus(decrypted_password)
    auth = f"{auth_user}:{auth_password}" if decrypted_password else auth_user
    target_host = host or profile.host
    target_port = port or profile.port
    suffix = f"/{target_database}" if target_database else ""
    return f"mysql+pymysql://{auth}@{target_host}:{target_port}{suffix}?charset=utf8mb4"


@contextmanager
def database_connection(profile: DatabaseConnectionProfile, *, database: str | None = None):
    if profile.db_type != "mysql":
        raise ValueError("Only MySQL profiles are supported in the workspace right now.")

    tunnel = None
    engine = None
    try:
        host = profile.host
        port = profile.port

        if profile.ssh_enabled:
            if SSHTunnelForwarder is None:
                raise RuntimeError("sshtunnel is not installed. Install dependencies before using SSH SQL profiles.")
            ssh_kwargs = {
                "ssh_address_or_host": (profile.ssh_host, profile.ssh_port or 22),
                "remote_bind_address": (profile.host, profile.port),
                "ssh_username": profile.ssh_username,
            }
            if profile.ssh_pkey_path:
                ssh_kwargs["ssh_pkey"] = profile.ssh_pkey_path
                if profile.ssh_pkey_passphrase:
                    ssh_kwargs["ssh_private_key_password"] = decrypt_secret(profile.ssh_pkey_passphrase)
            elif profile.ssh_password:
                ssh_kwargs["ssh_password"] = decrypt_secret(profile.ssh_password)
            tunnel = SSHTunnelForwarder(**ssh_kwargs)
            tunnel.start()
            host = "127.0.0.1"
            port = int(tunnel.local_bind_port)

        engine = create_engine(_build_mysql_url(profile, database=database, host=host, port=port), pool_pre_ping=True)
        with engine.begin() as connection:
            yield connection
    finally:
        if engine is not None:
            engine.dispose()
        if tunnel is not None:
            tunnel.stop()


def test_profile_connection(profile_id: str) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")
    with database_connection(profile, database=""):
        return {
            "status": "ok",
            "profile_id": profile_id,
        }


def inspect_profile(profile_id: str) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")

    with database_connection(profile, database="") as connection:
        inspector = inspect(connection)
        databases = [name for name in inspector.get_schema_names() if name not in {"information_schema", "performance_schema", "mysql", "sys"}]
        payload = []
        for database in databases:
            tables = inspector.get_table_names(schema=database)
            payload.append({
                "database": database,
                "tables": tables,
            })
        return {
            "profile": serialize_profile(profile),
            "databases": payload,
        }


def create_database(profile_id: str, database_name: str) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")
    database_name = _validate_identifier(database_name, "database name")
    with database_connection(profile, database="") as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    return inspect_profile(profile_id)


def create_table(profile_id: str, database_name: str, table_name: str, columns: list[dict]) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")
    database_name = _validate_identifier(database_name, "database name")
    table_name = _validate_identifier(table_name, "table name")
    if not columns:
        raise ValueError("At least one column is required")

    definitions = []
    for column in columns:
        column_name = _validate_identifier(column.get("name") or "", "column name")
        column_type = (column.get("type") or "VARCHAR(255)").upper()
        nullable = "" if column.get("nullable", True) else " NOT NULL"
        primary = " PRIMARY KEY" if column.get("primary_key") else ""
        definitions.append(f"`{column_name}` {column_type}{nullable}{primary}")

    statement = f"CREATE TABLE IF NOT EXISTS `{database_name}`.`{table_name}` ({', '.join(definitions)})"
    with database_connection(profile, database=database_name) as connection:
        connection.execute(text(statement))

    return preview_table(profile_id, database_name, table_name)


def preview_table(profile_id: str, database_name: str, table_name: str, limit: int = 50) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")
    database_name = _validate_identifier(database_name, "database name")
    table_name = _validate_identifier(table_name, "table name")

    with database_connection(profile, database=database_name) as connection:
        inspector = inspect(connection)
        columns = inspector.get_columns(table_name, schema=database_name)
        result = connection.execute(text(f"SELECT * FROM `{database_name}`.`{table_name}` LIMIT {max(1, min(limit, 200))}"))
        rows = [dict(row._mapping) for row in result]
        return {
            "database": database_name,
            "table": table_name,
            "columns": columns,
            "rows": rows,
        }


def insert_rows(profile_id: str, database_name: str, table_name: str, rows: list[dict]) -> dict:
    profile = get_profile_record(profile_id)
    if profile is None:
        raise ValueError("Profile not found")
    database_name = _validate_identifier(database_name, "database name")
    table_name = _validate_identifier(table_name, "table name")
    if not rows:
        raise ValueError("rows cannot be empty")

    with database_connection(profile, database=database_name) as connection:
        metadata = MetaData(schema=database_name)
        table = Table(table_name, metadata, autoload_with=connection)
        connection.execute(table.insert(), rows)

    return preview_table(profile_id, database_name, table_name)


def import_csv_rows(profile_id: str, database_name: str, table_name: str, csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    rows = [dict(row) for row in reader]
    return insert_rows(profile_id, database_name, table_name, rows)
