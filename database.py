from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# رابط قاعدة البيانات
DATABASE_URL = "postgresql://foursa_db_user:Cup5I8073i4K5qpHCWj7tr87WWmmalyb@dpg-d763ge450q8c73ft21m0-a/foursa_db"

# إنشاء المحرك (Engine)
engine = create_engine(DATABASE_URL)

# إنشاء جلسة الاتصال (Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# الكلاس الأساسي للجداول
Base = declarative_base()

# دالة الحصول على قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
