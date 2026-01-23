from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    # 进度字段 (Progress Fields)
    pc_search_progress = Column(String, default="0/90") 
    mobile_search_progress = Column(String, default="0/60")
    daily_set_status = Column(String, default="Incomplete") # 每日任务组状态
    last_run = Column(DateTime, default=datetime.datetime.utcnow)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True)
    account = Column(String, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    task_type = Column(String)
    task_name = Column(String)
    task_progress = Column(String)
    task_status = Column(String)
    task_start_time = Column(DateTime)
    task_end_time = Column(DateTime)

# 创建数据库引擎
engine = create_engine("sqlite:///./data/rewards.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()