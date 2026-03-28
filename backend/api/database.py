from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.db_workspace import (
    create_database,
    create_profile,
    create_table,
    import_csv_rows,
    inspect_profile,
    insert_rows,
    list_profiles,
    preview_table,
    test_profile_connection,
)

router = APIRouter(prefix="/api/db", tags=["database"])


class ConnectionProfilePayload(BaseModel):
    name: str = "MySQL Workspace"
    db_type: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = "root"
    password: str | None = None
    default_database: str | None = None
    ssh_enabled: bool = False
    ssh_host: str | None = None
    ssh_port: int | None = 22
    ssh_username: str | None = None
    ssh_password: str | None = None
    ssh_pkey_path: str | None = None
    ssh_pkey_passphrase: str | None = None
    save_password: bool = True


class CreateDatabasePayload(BaseModel):
    database_name: str


class CreateTablePayload(BaseModel):
    database_name: str
    table_name: str
    columns: list[dict[str, Any]] = Field(default_factory=list)


class InsertRowsPayload(BaseModel):
    database_name: str
    table_name: str
    rows: list[dict[str, Any]] = Field(default_factory=list)


class ImportCsvPayload(BaseModel):
    database_name: str
    table_name: str
    csv_text: str


def _translate_error(exc: Exception):
    raise HTTPException(status_code=400, detail=str(exc))


@router.get("/profiles")
async def get_profiles():
    return {
        "items": list_profiles(),
    }


@router.post("/profiles")
async def create_connection_profile(payload: ConnectionProfilePayload):
    try:
        return create_profile(payload.model_dump())
    except Exception as exc:
        _translate_error(exc)


@router.post("/profiles/{profile_id}/test")
async def test_connection_profile(profile_id: str):
    try:
        return test_profile_connection(profile_id)
    except Exception as exc:
        _translate_error(exc)


@router.get("/profiles/{profile_id}/schema")
async def get_profile_schema(profile_id: str):
    try:
        return inspect_profile(profile_id)
    except Exception as exc:
        _translate_error(exc)


@router.post("/profiles/{profile_id}/databases")
async def create_database_for_profile(profile_id: str, payload: CreateDatabasePayload):
    try:
        return create_database(profile_id, payload.database_name)
    except Exception as exc:
        _translate_error(exc)


@router.post("/profiles/{profile_id}/tables")
async def create_table_for_profile(profile_id: str, payload: CreateTablePayload):
    try:
        return create_table(profile_id, payload.database_name, payload.table_name, payload.columns)
    except Exception as exc:
        _translate_error(exc)


@router.get("/profiles/{profile_id}/tables/{database_name}/{table_name}")
async def get_table_preview(profile_id: str, database_name: str, table_name: str):
    try:
        return preview_table(profile_id, database_name, table_name)
    except Exception as exc:
        _translate_error(exc)


@router.post("/profiles/{profile_id}/rows")
async def insert_table_rows(profile_id: str, payload: InsertRowsPayload):
    try:
        return insert_rows(profile_id, payload.database_name, payload.table_name, payload.rows)
    except Exception as exc:
        _translate_error(exc)


@router.post("/profiles/{profile_id}/import-csv")
async def import_table_csv(profile_id: str, payload: ImportCsvPayload):
    try:
        return import_csv_rows(profile_id, payload.database_name, payload.table_name, payload.csv_text)
    except Exception as exc:
        _translate_error(exc)
