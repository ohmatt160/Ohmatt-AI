from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Index
from app.extensions import Base
from datetime import datetime, time


class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (
        Index("ix_tasks_user_date", "user_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    date = Column(DateTime, default=lambda: datetime.combine(datetime.utcnow().date(), time.min))
    time = Column(DateTime, default=datetime.utcnow)
    task = Column(Text, nullable=False)

    def __repr__(self):
        return f'<Task {self.task}>'
