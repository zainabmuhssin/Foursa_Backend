from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import User, JobSeekerDB, ManagerDB

router = APIRouter(prefix="/auth")


@router.get("/search")
def smart_search(
    query: str = Query(""),
    city: str = Query(""),
    role: str = Query(None),  # يتقبل None من الموبايل أو قيمة من الموقع
    db: Session = Depends(get_db),
):
    search_term = f"%{query}%"
    final_results = []

    # 1. البحث في جدول User (الموقع)
    site_query = db.query(User)

    # فلترة الـ role فقط إذا كان مرسلاً من المستخدم
    if role and role.strip():
        site_query = site_query.filter(User.role == role)

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
                "name": u.full_name,
                "job": u.info,
                "profile_image": u.profile_image,
                "user_image": u.profile_image,
                "city": u.city,
                "user_type": u.role,
            }
        )

    # 2. البحث في جداول التطبيق (الموبايل)
    # إذا لم يحدد role أو حدد jobseeker ابحث في الباحثين
    if role is None or role == "" or role == "jobseeker":
        app_seekers = (
            db.query(JobSeekerDB)
            .filter(
                or_(
                    JobSeekerDB.first_name.ilike(search_term),
                    JobSeekerDB.job_title.ilike(search_term),
                    JobSeekerDB.cv_content.ilike(search_term),
                )
            )
            .all()
        )
        for s in app_seekers:
            final_results.append(
                {
                    "id": s.id,
                    "name": f"{s.first_name} {s.last_name}",
                    "job": s.job_title,
                    "user_image": s.profile_image,
                    "cv_content": s.cv_content,
                    "user_type": "jobseeker",
                }
            )

    # إذا لم يحدد role أو حدد manager ابحث في المديرين
    if role is None or role == "" or role == "manager":
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
                    "name": f"{m.first_name} {m.last_name}",
                    "job": m.company_name,
                    "user_image": m.profile_image,
                    "user_type": "manager",
                }
            )

    return final_results
