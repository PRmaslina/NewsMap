from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import engine, Base, get_db
from models import Article as ArticleModel
from schemas import *
from crud import *

# Создаем таблицы при запуске
app = FastAPI(title="Database")

@app.on_event("startup")
def init_db():
    """Создание таблиц при старте"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

#########################
### Article Endpoints ###
#########################
@app.post("/articles", response_model=ArticleResponse)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    # Checking existance of article
    existing_article = ArticleCRUD.get_by_url(db, article.url)
    if existing_article:
        raise HTTPException(status_code=400, detail="Article already exists")
    
    # Creating article
    db_article = ArticleCRUD.create(db, article)
    return db_article

@app.get("/articles", response_model=List[ArticleResponse])
def get_articles(db: Session = Depends(get_db)):
    # Get all Articles
    articles = ArticleCRUD.get_all(db)
    return articles

@app.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    # Get Article by id
    article = ArticleCRUD.get_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.put("/articles/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, article_update: ArticleUpdate, db: Session = Depends(get_db)):
    # Update Article
    article = ArticleCRUD.update(db, article_id, article_update)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    # Delete Article
    success = ArticleCRUD.delete(db, article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted"}

@app.get("/")
def root():
    return {"message": "Hello World", "endpoints": ["/articles", "/articles/{id}", "/docs"]}