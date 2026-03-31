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
