<<<<<<< HEAD
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
=======
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# تأكدي أن الرابط يبدأ بـ postgresql:// وليس postgres://
DATABASE_URL = "postgresql://foursa_db_user:Cup5I8073i4K5qpHCWj7tr87WWmmalyb@dpg-d763ge450q8c73ft21m0-a/foursa_db"

# في الإصدارات الجديدة وقواعد PostgreSQL لا نحتاج connect_args
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
>>>>>>> 8ade551520ec340b2fc0393c6483a71d39d3a2cc
