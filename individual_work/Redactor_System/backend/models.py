from sqlalchemy import Column, Integer, Text, String, JSON
from database import Base

class RequestHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String, default="THESPIAN_CHAIN")
    prompt = Column(Text)
    result = Column(JSON)
