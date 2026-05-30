from sqlalchemy import Column, Integer, DateTime, Text
from app.extensions import Base
from datetime import datetime, time


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.combine(datetime.utcnow().date(), time.min))
    time = Column(DateTime, default=datetime.utcnow)
    task = Column(Text, nullable=False)

    def __repr__(self):
        return f'<Task {self.task}>'