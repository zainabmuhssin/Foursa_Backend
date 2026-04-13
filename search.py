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
    role: str = Query(None),
    db: Session = Depends(get_db),
):
    search_term = f"%{query}%"
    final_results = []

    # 1. البحث للموقع (جدول User) - مع فلترة المدينة والـ Role
    site_query = db.query(User)

    if role:
        site_query = site_query.filter(User.role == role)
    if city:
        site_query = site_query.filter(User.city == city)
    if query:
        site_query = site_query.filter(
            or_(User.full_name.ilike(search_term), User.info.ilike(search_term))
        )

    for u in site_query.all():
        final_results.append(
            {
                "id": u.id,
                "name": u.full_name,
                "job": u.info,
                "profile_image": u.profile_image,
                "user_image": u.profile_image,
                "cv_content": u.info,  # ممكن نستخدم نفس الحقل لعرض معلومات إضافية
                "cv_path": u.cv_path,  # إذا حابة تعرضين رابط السي في
                "city": u.city,
                "user_type": u.role,
            }
        )

    # 2. البحث للتطبيق (الموبايل) - جداول الباحثين والمديرين
    # ملاحظة: الموبايل ما يرسل City حالياً حسب كود Flutter مالتج، بس السيرفر جاهز إذا ضفتيها مستقبلاً

    # إذا الباحث كاعد يبحث (يريد يشوف شركات)
    if role == "jobseeker" or role is None:
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

    # إذا المدير كاعد يبحث (يريد يشوف كفاءات وسير ذاتية)
    if role == "manager" or role is None:
        app_seekers = (
            db.query(JobSeekerDB)
            .filter(
                or_(
                    JobSeekerDB.first_name.ilike(search_term),
                    JobSeekerDB.job_title.ilike(search_term),
                    JobSeekerDB.cv_content.ilike(
                        search_term
                    ),  # البحث الذكي داخل السي في
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

    return final_results
