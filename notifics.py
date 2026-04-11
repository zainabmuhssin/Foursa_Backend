from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from chance_backend import models
from models import PostDB

# استوردِ الملفات الخاصة بكِ (تأكدي من الأسماء)
from database import get_db
from models import NotificationDB, JobSeekerDB, ManagerDB, PostDB

# import models  # استيراد ملف الموديلات الخاص بكِ

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/{user_id}")
def get_notifications(user_id: int, user_type: str, db: Session = Depends(get_db)):
    notifications = (
        db.query(NotificationDB)
        .filter(
            NotificationDB.user_id == user_id, NotificationDB.user_type == user_type
        )
        .order_by(NotificationDB.create_at.desc())
        .all()
    )

    result = []
    for n in notifications:
        post_info = None
        extra_data = {}

        # --- الجزء الخاص بصورة المتقدم الجديد (إشعار التقديم) ---
        if n.type == "review_applicant":
            seeker = (
                db.query(models.JobSeekerDB)
                .filter(models.JobSeekerDB.id == n.sender_id)
                .first()
            )
            extra_data = {
                "profile_image": seeker.profile_image if seeker else None,
                "sender_id": str(n.sender_id),
                "sender_type": n.sender_type,
            }

        # --- جزء الرسائل (بدون تغيير كما طلبتِ) ---
        elif n.type == "message":
            # 1. جلب بيانات المرسل (سواء كان باحث أو مدير)
            if n.sender_type == "jobseeker":
                sender = (
                    db.query(models.JobSeekerDB)
                    .filter(models.JobSeekerDB.id == n.sender_id)
                    .first()
                )
            else:
                sender = (
                    db.query(models.ManagerDB)
                    .filter(models.ManagerDB.id == n.sender_id)
                    .first()
                )

            # 2. تجهيز البيانات الإضافية للإشعار
            extra_data = {
                "user_id": str(n.sender_id),
                "user_type": str(n.sender_type),
                "user_name": n.title.replace("رسالة جديدة من ", ""),
                # ✅ هنا السحر: نرسل اسم الصورة لكي تظهر في دائرة الإشعار
                "profile_image": sender.profile_image if sender else None,
            }

        # --- جزء الوظائف الجديدة (للباحثين المتابعين) ---
        elif n.type == "new_job":
            post = db.query(models.PostDB).filter(models.PostDB.id == n.post_id).first()
            if post:
                # نرسل بيانات المنشور كاملة لكي تفتح صفحة JobDetailsPage فوراً
                post_info = {
                    "id": post.id,
                    "userId": post.user_id,  # مهم للبروفايل
                    "userName": post.user_name,
                    "userImage": post.user_image,
                    "title": post.title,
                    "content": post.content,
                    "postImage": post.post_image,
                    "createAt": post.create_at.isoformat(),
                    "userType": post.user_type,
                }

        # --- جزء حالة الطلب (عندما يقبل أو يرفض المدير) ---
        elif n.type == "job_status":
            post = db.query(models.PostDB).filter(models.PostDB.id == n.post_id).first()
            manager = (
                db.query(models.ManagerDB)
                .filter(models.ManagerDB.id == n.sender_id)
                .first()
            )

            # نرسل الـ status الحقيقي من الـ body أو حقل إضافي
            # نفترض أن n.body يحتوي على "accepted" أو "rejected" أو نص عربي
            extra_data = {
                "job_id": str(n.post_id),
                "job_title": post.title if post else "فرصة عمل",
                "company_name": manager.company_name if manager else "شركة",
                "status": (
                    "accepted" if "تم قبول" in n.title else "rejected"
                ),  # استنتاج الحالة من العنوان
                "manager_id": str(n.sender_id),
            }

        result.append(
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "time": n.create_at.isoformat(),
                "isRead": n.is_read,
                "post_data": post_info,
                "extra_data": extra_data,
            }
        )

    return {"status": "success", "data": result}


@router.delete("/delete/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    try:
        # البحث عن الإشعار في قاعدة البيانات
        db_notification = (
            db.query(NotificationDB)
            .filter(NotificationDB.id == notification_id)
            .first()
        )

        # إذا لم يتم العثور على الإشعار
        if not db_notification:
            raise HTTPException(status_code=404, detail="الإشعار غير موجود")

        # تنفيذ عملية الحذف
        db.delete(db_notification)
        db.commit()

        return {"status": "success", "message": "تم حذف الإشعار بنجاح"}

    except Exception as e:
        db.rollback()  # للتراجع عن العملية في حال حدوث خطأ مفاجئ
        print(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء الحذف")
