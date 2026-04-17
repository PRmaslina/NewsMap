from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Параметры подключения
DATABASE_URL = "postgresql://user:password@database:5432/database"

# Создаем engine
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии БД (та самая зависимость)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()