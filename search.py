from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import JobSeekerDB, ManagerDB

router = APIRouter(prefix="/search", tags=["Search"])

# تأكدي أن هذا الرابط يطابق إعدادات ريندر لديكِ
BASE_URL = "https://foursa-backend.onrender.com/uploads/"


@router.get("/search")
def smart_search(query: str = Query(...), db: Session = Depends(get_db)):
    # تحويل النص ليكون متوافقاً مع البحث الجزئي
    search_term = f"%{query}%"

    # 1. البحث في جدول الباحثين عن عمل (JobSeekers)
    # تم حذف شرط الـ city تماماً لحل خطأ NameError
    seekers = (
        db.query(JobSeekerDB)
        .filter(
            (JobSeekerDB.first_name.ilike(search_term))
            | (JobSeekerDB.last_name.ilike(search_term))
            | (JobSeekerDB.job_title.ilike(search_term))
            | (JobSeekerDB.cv_content.ilike(search_term))
        )
        .all()
    )

    # 2. البحث في جدول أصحاب العمل (Managers)
    managers = (
        db.query(ManagerDB)
        .filter(
            (ManagerDB.first_name.ilike(search_term))
            | (ManagerDB.last_name.ilike(search_term))
            | (ManagerDB.company_name.ilike(search_term))
        )
        .all()
    )

    final_results = []

    # تنسيق نتائج الباحثين
    for s in seekers:
        final_results.append(
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "job": s.job_title or "Job Seeker",
                "cv_content": s.cv_content or "",
                "user_image": s.profile_image if s.profile_image else "",
                "user_type": "jobseeker",
                "cv_file": s.cv_file or "",
            }
        )

    # تنسيق نتائج أصحاب العمل
    for m in managers:
        final_results.append(
            {
                "id": m.id,
                "name": f"{m.first_name} {m.last_name}",
                "job": m.company_name or "Company Manager",
                "cv_content": m.business_type or "Manager",
                "user_image": m.profile_image if m.profile_image else "",
                "user_type": "manager",
                "cv_file": "",
            }
        )

    return final_results
