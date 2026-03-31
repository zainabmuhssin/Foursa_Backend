from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# رابط قاعدة البيانات
DATABASE_URL = "sqlite:///./jobs_pro.db"

# إنشاء المحرك (Engine)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# إنشاء جلسة الاتصال (Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# الكلاس الأساسي للجداول
Base = declarative_base()


# دالة الحصول على قاعدة البيانات (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
