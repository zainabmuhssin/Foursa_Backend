from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
import models
from database import get_db
from models import FollowDB, JobSeekerDB, ManagerDB, get_db
from passlib.context import CryptContext
from security import get_password_hash, verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/settings",  # هذا يعني أن كل الروابط ستبدأ بـ /settings
    tags=["Settings"],  # لتنظيمها في Swagger UI
)


# 1. دالة تحديث كلمة السر


@router.put("/update-password")
async def update_password(
    user_id: int = Form(...),
    account_type: str = Form(...),
    old_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1. البحث
    if account_type == "manager":
        user = db.query(models.ManagerDB).filter(models.ManagerDB.id == user_id).first()
    else:
        user = (
            db.query(models.JobSeekerDB)
            .filter(models.JobSeekerDB.id == user_id)
            .first()
        )

    # 2. طباعة للتأكد من وصول الطلب أصلاً
    print(f"DEBUG: Received request for ID {user_id} and Type {account_type}")

    if not user:
        print(f"DEBUG: User {user_id} not found in {account_type} table")
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # 3. المقارنة
    if not verify_password(old_password, user.password):
        print(f"DEBUG: Old password does not match for user {user_id}")
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    user.password = get_password_hash(new_password)
    db.commit()
    return {"status": "success", "message": "تم تحديث كلمة المرور بنجاح"}


# 2. دالة حذف الحساب
@router.delete("/delete-account/{user_id}")
async def delete_account(user_id: int, db: Session = Depends(get_db)):
    # محاولة حذف من جدول المديرين أولاً
    user = db.query(models.ManagerDB).filter(models.ManagerDB.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return {"status": "success", "message": "تم حذف حساب المدير بنجاح"}

    # إذا لم يكن مدير، حاول حذف من جدول الباحثين عن عمل
    user = db.query(models.JobSeekerDB).filter(models.JobSeekerDB.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return {"status": "success", "message": "تم حذف حساب الباحث عن عمل بنجاح"}

    raise HTTPException(status_code=404, detail="المستخدم غير موجود")


@router.get("/user_details/{user_id}")
def get_user_details(
    user_id: int,
    account_type: str,
    my_id: int = None,
    my_type: str = None,
    db: Session = Depends(get_db),
):
    user = None
    if account_type == "jobseeker":
        user = db.query(models.JobSeekerDB).filter(models.JobSeekerDB.id == user_id).first()
    elif account_type == "manager":
        user = db.query(models.ManagerDB).filter(models.ManagerDB.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. التحقق من حالة المتابعة
    is_followed = False
    if my_id and my_type:
        check = db.query(models.FollowDB).filter(
            models.FollowDB.follower_id == my_id,
            models.FollowDB.follower_type == my_type,
            models.FollowDB.following_id == user_id,
            models.FollowDB.following_type == account_type,
        ).first()
        is_followed = True if check else False

    # 2. حساب العدادات
    followers_count_real = db.query(models.FollowDB).filter(
        models.FollowDB.following_id == user_id,
        models.FollowDB.following_type == account_type,
    ).count()

    following_count_real = db.query(models.FollowDB).filter(
        models.FollowDB.follower_id == user_id,
        models.FollowDB.follower_type == account_type,
    ).count()

    # --- بداية الكود الجديد الذي سألتي عنه ---
    res_data = {
        "id": user.id,
        "name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "profile_image": user.profile_image,
        "is_following": is_followed,
        "followersCount": followers_count_real,
        "followingCount": following_count_real,
    }

    if account_type == "jobseeker":
        # تأكدي أن الأسماء (job_title, cv_file, cv_content) تطابق الموديل عندك
        res_data["job_title"] = getattr(user, "job_title", "")
        res_data["cv_file"] = getattr(user, "cv_file", "") # هذا هو السطر المهم لفتح الـ PDF
        res_data["cv_content"] = getattr(user, "cv_content", "")
    elif account_type == "manager":
        res_data["company_name"] = getattr(user, "company_name", "")
        res_data["business_type"] = getattr(user, "business_type", "")

    return res_data