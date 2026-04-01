<<<<<<< HEAD
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
import models  # استيراد ملف الموديلات الخاص بكِ
from models import get_db, NotificationDB, JobSeekerDB  # استيراد دالة قاعدة البيانات


router = APIRouter(prefix="/apps", tags=["Applications"])


@router.get("/get-applicants/{manager_id}")
async def get_applicants(manager_id: int, db: Session = Depends(get_db)):
    # جلب الطلبات الخاصة بهذا المدير مع بيانات الباحثين (للحصول على السي في والاسم)
    results = (
        db.query(models.ApplicationDB, models.JobSeekerDB)
        .join(
            models.JobSeekerDB,
            models.ApplicationDB.jobseeker_id == models.JobSeekerDB.id,
        )
        .filter(models.ApplicationDB.manager_id == manager_id)
        .all()
    )

    applicants_list = []
    for app, seeker in results:
        applicants_list.append(
            {
                "app_id": app.id,
                "seeker_id": seeker.id,  # <<< هذا السطر المفقود والجوهري!
                "seeker_name": f"{seeker.first_name} {seeker.last_name}",
                "seeker_email": seeker.email,
                "job_title": seeker.job_title,
                "cv_content": seeker.cv_content,
                "cv_file": seeker.cv_file,
                "status": app.status,
                "profile_image": seeker.profile_image,
            }
        )
    return applicants_list


@router.post("/apply-job")
async def apply_job(
    job_id: int = Form(...),
    jobseeker_id: int = Form(...),
    db: Session = Depends(get_db),
):
    # 1. جلب بيانات الوظيفة لمعرفة من هو المدير (الناشر)
    job_post = db.query(models.PostDB).filter(models.PostDB.id == job_id).first()
    if not job_post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    # 🔥 جلب بيانات الباحث المحدد لكي نستخدم اسمه في الإشعار
    seeker = (
        db.query(models.JobSeekerDB)
        .filter(models.JobSeekerDB.id == jobseeker_id)
        .first()
    )
    if not seeker:
        raise HTTPException(status_code=404, detail="الباحث غير موجود")

    # 2. التأكد إذا كان المستخدم قدم مسبقاً
    existing_apply = (
        db.query(models.ApplicationDB)
        .filter(
            models.ApplicationDB.post_id == job_id,
            models.ApplicationDB.jobseeker_id == jobseeker_id,
        )
        .first()
    )

    if existing_apply:
        return {"status": "exists", "message": "لقد قمت بالتقديم مسبقاً لهذه الوظيفة"}

    # 3. إضافة الطلب
    new_application = models.ApplicationDB(
        post_id=job_id,
        jobseeker_id=jobseeker_id,
        manager_id=job_post.user_id,
    )
    db.add(new_application)

    # 4. إضافة الإشعار (تم تصحيح طريقة كتابة الاسم هنا)
    new_notification = NotificationDB(
        user_id=job_post.user_id,
        user_type="manager",
        title="متقدم جديد لوظيفتك",
        # ✅ استخدمنا seeker.first_name بدل اسم الجدول العام
        body=f"قام {seeker.first_name} {seeker.last_name} بالتقديم على وظيفة {job_post.title}",
        type="review_applicant",
        sender_id=jobseeker_id,
        sender_type="jobseeker",
        post_id=job_id,
        is_read=False,
    )
    db.add(new_notification)

    db.commit()
    return {
        "status": "success",
        "message": "Application submitted and notification sent",
    }


@router.get("/get-status/{job_id}/{seeker_id}")
async def get_application_status(
    job_id: int, seeker_id: int, db: Session = Depends(get_db)
):
    # جلب طلب التقديم إن وُجد
    application = (
        db.query(models.ApplicationDB)
        .filter(models.ApplicationDB.post_id == job_id)
        .filter(models.ApplicationDB.jobseeker_id == seeker_id)
        .first()
    )

    if not application:
        # لم يتم العثور على طلب التقديم
        raise HTTPException(status_code=404, detail="Application not found")

    # جلب بيانات المنشور والمدير
    post = db.query(models.PostDB).filter(models.PostDB.id == job_id).first()
    manager = None
    if application.manager_id:
        manager = (
            db.query(models.ManagerDB)
            .filter(models.ManagerDB.id == application.manager_id)
            .first()
        )

    result = {
        "status": application.status,
        "apply_date": (
            application.apply_date.isoformat() if application.apply_date else None
        ),
        "job_title": post.title if post else None,
        "company_name": (
            manager.company_name
            if manager and manager.company_name
            else (post.user_name if post else None)
        ),
        "manager": {
            "id": manager.id if manager else None,
            "name": f"{manager.first_name} {manager.last_name}" if manager else None,
            "email": manager.email if manager else None,
            "profile_image": (
                f"https://foursa-backend.onrender.com/{manager.profile_image}"
                if manager and manager.profile_image
                else None
            ),
        },
    }

    return result
=======
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
import models  # استيراد ملف الموديلات الخاص بكِ
from models import get_db, NotificationDB, JobSeekerDB  # استيراد دالة قاعدة البيانات


router = APIRouter(prefix="/apps", tags=["Applications"])


@router.get("/get-applicants/{manager_id}")
async def get_applicants(manager_id: int, db: Session = Depends(get_db)):
    # جلب الطلبات الخاصة بهذا المدير مع بيانات الباحثين (للحصول على السي في والاسم)
    results = (
        db.query(models.ApplicationDB, models.JobSeekerDB)
        .join(
            models.JobSeekerDB,
            models.ApplicationDB.jobseeker_id == models.JobSeekerDB.id,
        )
        .filter(models.ApplicationDB.manager_id == manager_id)
        .all()
    )

    applicants_list = []
    for app, seeker in results:
        applicants_list.append(
            {
                "app_id": app.id,
                "seeker_id": seeker.id,  # <<< هذا السطر المفقود والجوهري!
                "seeker_name": f"{seeker.first_name} {seeker.last_name}",
                "seeker_email": seeker.email,
                "job_title": seeker.job_title,
                "cv_content": seeker.cv_content,
                "cv_file": seeker.cv_file,
                "status": app.status,
                "profile_image": seeker.profile_image,
            }
        )
    return applicants_list


@router.post("/apply-job")
async def apply_job(
    job_id: int = Form(...),
    jobseeker_id: int = Form(...),
    db: Session = Depends(get_db),
):
    # 1. جلب بيانات الوظيفة لمعرفة من هو المدير (الناشر)
    job_post = db.query(models.PostDB).filter(models.PostDB.id == job_id).first()
    if not job_post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    # 🔥 جلب بيانات الباحث المحدد لكي نستخدم اسمه في الإشعار
    seeker = (
        db.query(models.JobSeekerDB)
        .filter(models.JobSeekerDB.id == jobseeker_id)
        .first()
    )
    if not seeker:
        raise HTTPException(status_code=404, detail="الباحث غير موجود")

    # 2. التأكد إذا كان المستخدم قدم مسبقاً
    existing_apply = (
        db.query(models.ApplicationDB)
        .filter(
            models.ApplicationDB.post_id == job_id,
            models.ApplicationDB.jobseeker_id == jobseeker_id,
        )
        .first()
    )

    if existing_apply:
        return {"status": "exists", "message": "لقد قمت بالتقديم مسبقاً لهذه الوظيفة"}

    # 3. إضافة الطلب
    new_application = models.ApplicationDB(
        post_id=job_id,
        jobseeker_id=jobseeker_id,
        manager_id=job_post.user_id,
    )
    db.add(new_application)

    # 4. إضافة الإشعار (تم تصحيح طريقة كتابة الاسم هنا)
    new_notification = NotificationDB(
        user_id=job_post.user_id,
        user_type="manager",
        title="متقدم جديد لوظيفتك",
        # ✅ استخدمنا seeker.first_name بدل اسم الجدول العام
        body=f"قام {seeker.first_name} {seeker.last_name} بالتقديم على وظيفة {job_post.title}",
        type="review_applicant",
        sender_id=jobseeker_id,
        sender_type="jobseeker",
        post_id=job_id,
        is_read=False,
    )
    db.add(new_notification)

    db.commit()
    return {
        "status": "success",
        "message": "Application submitted and notification sent",
    }


@router.get("/get-status/{job_id}/{seeker_id}")
async def get_application_status(
    job_id: int, seeker_id: int, db: Session = Depends(get_db)
):
    # جلب طلب التقديم إن وُجد
    application = (
        db.query(models.ApplicationDB)
        .filter(models.ApplicationDB.post_id == job_id)
        .filter(models.ApplicationDB.jobseeker_id == seeker_id)
        .first()
    )

    if not application:
        # لم يتم العثور على طلب التقديم
        raise HTTPException(status_code=404, detail="Application not found")

    # جلب بيانات المنشور والمدير
    post = db.query(models.PostDB).filter(models.PostDB.id == job_id).first()
    manager = None
    if application.manager_id:
        manager = (
            db.query(models.ManagerDB)
            .filter(models.ManagerDB.id == application.manager_id)
            .first()
        )

    result = {
        "status": application.status,
        "apply_date": (
            application.apply_date.isoformat() if application.apply_date else None
        ),
        "job_title": post.title if post else None,
        "company_name": (
            manager.company_name
            if manager and manager.company_name
            else (post.user_name if post else None)
        ),
        "manager": {
            "id": manager.id if manager else None,
            "name": f"{manager.first_name} {manager.last_name}" if manager else None,
            "email": manager.email if manager else None,
            "profile_image": (
                f"http://192.168.1.84:8080/{manager.profile_image}"
                if manager and manager.profile_image
                else None
            ),
        },
    }

    return result
>>>>>>> 8ade551520ec340b2fc0393c6483a71d39d3a2cc
