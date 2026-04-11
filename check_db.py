import sqlite3

conn = sqlite3.connect("jobs_pro.db")
cursor = conn.cursor()

# عرض الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("الجداول الموجودة:")
for table in tables:
    print(f"- {table[0]}")

# التحقق من جدول users
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("\nأعمدة جدول users:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()
