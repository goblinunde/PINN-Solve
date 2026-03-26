from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Float, JSON, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "pinn_solve.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

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


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
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
