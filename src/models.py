from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False, unique=True)
    subtitle = Column(String, nullable=True)
    position = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=True)
    tags = Column(String, nullable=True)

    #долгота и широта
    latitude = Column(Float, nullable=True)   
    longitude = Column(Float, nullable=True)  

    def __repr__(self):
        return f"<Article(id={self.id}, url={self.url}, date={self.date}, text={self.text})>"