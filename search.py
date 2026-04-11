from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import JobSeekerDB, ManagerDB  # الأسماء من صورتك

router = APIRouter()

BASE_URL = "https://foursa-backend.onrender.com/uploads/"


@router.get("/search")
def smart_search(query: str = Query(...), db: Session = Depends(get_db)):
    search_term = f"%{query}%"

    # 1. البحث في جدول الباحثين عن عمل (JobSeekers)
    # البحث في: first_name, last_name, job_title, cv_content
    seekers_query = db.query(JobSeekerDB).filter(
        (JobSeekerDB.first_name.like(search_term))
        | (JobSeekerDB.last_name.like(search_term))
        | (JobSeekerDB.job_title.like(search_term))
        | (JobSeekerDB.cv_content.like(search_term))
    )
    if city:
        seekers_query = seekers_query.filter(JobSeekerDB.city == city)
    seekers = seekers_query.all()

    # 2. البحث في جدول المديرين/الشركات (Managers)
    # البحث في: first_name, last_name, company_name
    managers_query = db.query(ManagerDB).filter(
        (ManagerDB.first_name.like(search_term))
        | (ManagerDB.last_name.like(search_term))
        | (ManagerDB.company_name.like(search_term))
    )
    if city:
        managers_query = managers_query.filter(ManagerDB.city == city)
    managers = managers_query.all()

    # تجميع النتائج في قائمة واحدة موحدة للفلاتر
    final_results = []

    if role in ["jobseeker", "all"]:
        for s in seekers:
            final_results.append(
                {
                    "id": s.id,
                    "name": f"{s.first_name} {s.last_name}",
                    "job": s.job_title or "No Title",
                    "cv_content": s.cv_content or "",
                    "user_image": (
                        f"{BASE_URL}{s.profile_image}" if s.profile_image else ""
                    ),
                    "user_type": "jobseeker",
                    "cv_path": s.cv_file,
                    "role": "jobseeker",
                    "city": s.city,
                }
            )

    if role in ["manager", "all"]:
        for m in managers:
            final_results.append(
                {
                    "id": m.id,
                    "name": f"{m.first_name} {m.last_name}",
                    "job": m.company_name or "Manager",
                    "cv_content": m.business_type
                    or "",  # استخدمنا نوع العمل كـ CV مختصر للمدير
                    "user_image": (
                        f"{BASE_URL}{m.profile_image}" if m.profile_image else ""
                    ),
                    "user_type": "manager",
                    "cv_path": None,
                    "role": "manager",
                    "city": m.city,
                }
            )

    return final_results
