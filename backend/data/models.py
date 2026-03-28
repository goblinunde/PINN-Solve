from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent


def build_database_url() -> str:
    explicit_url = os.getenv("PINNSOLVER_DATABASE_URL")
    if explicit_url:
        return explicit_url

    backend = (os.getenv("PINNSOLVER_DB_BACKEND") or "sqlite").lower()
    if backend == "mysql":
        user = os.getenv("PINNSOLVER_DB_USER") or "root"
        password = os.getenv("PINNSOLVER_DB_PASSWORD") or ""
        host = os.getenv("PINNSOLVER_DB_HOST") or "127.0.0.1"
        port = os.getenv("PINNSOLVER_DB_PORT") or "3306"
        database = os.getenv("PINNSOLVER_DB_NAME") or "PINNSOLVER"
        auth = f"{user}:{password}" if password else user
        return f"mysql+pymysql://{auth}@{host}:{port}/{database}?charset=utf8mb4"

    database_path = os.getenv("PINNSOLVER_SQLITE_PATH") or str(BASE_DIR / "pinn_solve.db")
    return f"sqlite:///{database_path}"


DATABASE_URL = build_database_url()
CELERY_RESULT_BACKEND_URL = f"db+{DATABASE_URL}"

Base = declarative_base()


class Problem(Base):
    __tablename__ = "problems"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TrainingTask(Base):
    __tablename__ = "training_jobs"

    task_id = Column(String, primary_key=True)
    celery_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    pde = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="queued")
    progress = Column(Float, nullable=False, default=0.0)
    mode = Column(String, nullable=False, default="pending")
    config = Column(JSON, nullable=False, default=dict)
    losses = Column(JSON, nullable=False, default=list)
    solution = Column(JSON)
    note = Column(Text)
    error = Column(Text)
    cancel_requested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)


class WorkerState(Base):
    __tablename__ = "worker_states"

    worker_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="offline")
    last_heartbeat_at = Column(DateTime)
    last_task_id = Column(String)
    last_error = Column(Text)
    started_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TrainingDataset(Base):
    __tablename__ = "training_datasets"

    dataset_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    pde_kind = Column(String, nullable=False, default="generic")
    input_dim = Column(Integer, nullable=False, default=0)
    sample_count = Column(Integer, nullable=False, default=0)
    description = Column(Text)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DatabaseConnectionProfile(Base):
    __tablename__ = "db_connection_profiles"

    profile_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False, default="mysql")
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=3306)
    username = Column(String, nullable=False)
    password = Column(Text)
    default_database = Column(String)
    ssh_enabled = Column(Boolean, nullable=False, default=False)
    ssh_host = Column(String)
    ssh_port = Column(Integer)
    ssh_username = Column(String)
    ssh_password = Column(Text)
    ssh_pkey_path = Column(Text)
    ssh_pkey_passphrase = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


engine_options = {}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def init_db():
    Base.metadata.create_all(engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
