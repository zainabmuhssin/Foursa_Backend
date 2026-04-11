from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import JobSeekerDB, ManagerDB

# لا تضعي prefix هنا إذا كان الـ signup شغال بدون prefix
router = APIRouter()


@router.get("/search")  # الرابط سيكون مباشرة /search
def smart_search(query: str = Query(""), db: Session = Depends(get_db)):
    search_term = f"%{query}%"

    # البحث في الجداول (تأكدي أن أسماء الجداول مطابقة للـ Models)
    seekers = (
        db.query(JobSeekerDB)
        .filter(
            or_(
                JobSeekerDB.first_name.ilike(search_term),
                JobSeekerDB.last_name.ilike(search_term),
                JobSeekerDB.job_title.ilike(search_term),
                JobSeekerDB.cv_content.ilike(search_term),
            )
        )
        .all()
    )

    managers = (
        db.query(ManagerDB)
        .filter(
            or_(
                ManagerDB.first_name.ilike(search_term),
                ManagerDB.last_name.ilike(search_term),
                ManagerDB.company_name.ilike(search_term),
                ManagerDB.business_type.ilike(search_term),
            )
        )
        .all()
    )

    results = []
    for s in seekers:
        results.append(
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "job": s.job_title,
                "user_type": "jobseeker",
            }
        )
    for m in managers:
        results.append(
            {
                "id": m.id,
                "name": f"{m.first_name} {m.last_name}",
                "job": m.company_name,
                "user_type": "manager",
            }
        )

    return results
