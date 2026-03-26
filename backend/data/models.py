from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer)
    status = Column(String)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine("sqlite:///pinn_solve.db")
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
