from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import User, JobSeekerDB, ManagerDB

router = APIRouter(prefix="/auth")


@router.get("/search")  # هذا الرابط راح يخدم الموقع والتطبيق
def smart_search(
    query: str = Query(""),
    city: str = Query(""),
    role: str = Query(None),
    db: Session = Depends(get_db),
):
    search_term = f"%{query}%"
    final_results = []

    # 1. البحث في جدول الموقع (User)
    # ضفنا فلترة المدينة والـ role حتى الموقع ما يخرب
    site_query = db.query(User).filter(User.role == role)
    if query:
        site_query = site_query.filter(
            or_(User.full_name.ilike(search_term), User.info.ilike(search_term))
        )
    if city:
        site_query = site_query.filter(User.city == city)

    for u in site_query.all():
        final_results.append(
            {
                "id": u.id,
                "full_name": u.full_name,  # للموقع
                "name": u.full_name,  # للتطبيق
                "info": u.info,  # للموقع
                "job": u.info,  # للتطبيق
                "profile_image": u.profile_image,
                "user_image": u.profile_image,
                "city": u.city,
                "cv_text": u.cv_text,
                "cv_path": u.cv_path,
                "user_type": u.role,
            }
        )

    # 2. البحث في جداول التطبيق (فقط إذا كان الـ role مطابق)
    if role is None or role == "jobseeker":
        app_seekers = (
            db.query(JobSeekerDB)
            .filter(
                or_(
                    JobSeekerDB.first_name.ilike(search_term),
                    JobSeekerDB.job_title.ilike(search_term),
                    JobSeekerDB.cv_file.ilike(search_term),
                    JobSeekerDB.cv_content.ilike(search_term),
                )
            )
            .all()
        )
        for s in app_seekers:
            final_results.append(
                {
                    "id": s.id,
                    "full_name": f"{s.first_name} {s.last_name}",
                    "name": f"{s.first_name} {s.last_name}",
                    "info": s.job_title,
                    "job": s.job_title,
                    "profile_image": s.profile_image,
                    "user_image": s.profile_image,
                    "cv_file": s.cv_file,
                    "cv_content": s.cv_content,
                    "user_type": "jobseeker",
                }
            )

    elif role is None or role == "manager":
        app_managers = (
            db.query(ManagerDB)
            .filter(
                or_(
                    ManagerDB.first_name.ilike(search_term),
                    ManagerDB.company_name.ilike(search_term),
                )
            )
            .all()
        )
        for m in app_managers:
            final_results.append(
                {
                    "id": m.id,
                    "full_name": f"{m.first_name} {m.last_name}",
                    "name": f"{m.first_name} {m.last_name}",
                    "info": m.company_name,
                    "job": m.company_name,
                    "profile_image": m.profile_image,
                    "user_image": m.profile_image,
                    "user_type": "manager",
                }
            )

    return final_results
