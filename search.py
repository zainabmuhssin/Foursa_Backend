from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import User  # نستخدم جدول User الموحد كما في الموقع

router = APIRouter(prefix="/auth")


@router.get("/search")
def smart_search(query: str = Query(""), db: Session = Depends(get_db)):
    search_term = f"%{query}%"

    # البحث الذكي: يبحث في الاسم، المعلومات، والمدينة داخل استعلام واحد
    results = (
        db.query(User)
        .filter(
            or_(
                User.full_name.ilike(search_term),
                User.info.ilike(search_term),
                User.city.ilike(search_term),  # يبحث في المدينة من خلال نص البحث العادي
            )
        )
        .all()
    )

    output = []
    for user in results:
        output.append(
            {
                "id": user.id,
                "name": user.full_name,
                "job": user.info or "No Title",
                "user_image": user.profile_image or "",
                "user_type": user.role,  # هذا ضروري للتفرقة عند الضغط على البروفايل
                "city": user.city or "",
            }
        )

    return output
