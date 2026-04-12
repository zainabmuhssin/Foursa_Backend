from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
import models
from database import get_db
import os
import shutil
import uuid
from models import (
    FollowDB,
    JobSeekerDB,
    ManagerDB,
    PostDB,
    SavedPostDB,
)

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/add-post")
async def add_post(
    title: str = Form(...),
    content: str = Form(...),
    user_id: int = Form(...),
    user_type: str = Form(...),  # تم التعديل: استلام نوع الحساب من فلاتر
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # تعديل احترافي: استخدام اسم فريد لكل صورة لتجنب التكرار
    extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = f"uploads/{unique_filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_post = models.PostDB(
        title=title,
        content=content,
        user_id=user_id,
        user_type=user_type,  # تم التعديل: حفظ نوع الحساب في الجدول
        post_image=file_path,
        likes_count=0,
        comments_count=0,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"status": "success", "post_id": new_post.id}


@router.put("/edit-post/{post_id}")
async def edit_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    post = db.query(models.PostDB).filter(models.PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.title = title
    post.content = content

    if file:
        # مسح الصورة القديمة إذا كانت موجودة لتقليل مساحة السيرفر
        if post.post_image and os.path.exists(post.post_image):
            os.remove(post.post_image)

        extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_path = f"uploads/{unique_filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        post.post_image = file_path

    db.commit()
    return {"status": "success", "message": "Post updated"}


@router.get("/my-profile-posts/{user_id}/{account_type}")
async def get_user_posts(
    user_id: int, account_type: str, db: Session = Depends(get_db)
):
    # 1. جلب المنشورات التي تطابق الـ ID ونوع الحساب معاً
    posts = (
        db.query(models.PostDB)
        .filter(models.PostDB.user_id == user_id)
        .filter(models.PostDB.user_type == account_type)  # الفلتر الأهم لمنع الاختلاط
        .order_by(models.PostDB.id.desc())
        .all()
    )

    output = []
    base_url = "https://foursa-backend.onrender.com"

    for p in posts:
        # بما أن جدول PostDB يحتوي على الاسم والصورة بالفعل، يمكننا استخدامهما مباشرة
        # أو الاستمرار بجلب البيانات المحدثة من جداول المستخدمين لضمان الدقة
        if p.user_type == "manager":
            user_data = (
                db.query(models.ManagerDB)
                .filter(models.ManagerDB.id == p.user_id)
                .first()
            )
        else:
            user_data = (
                db.query(models.JobSeekerDB)
                .filter(models.JobSeekerDB.id == p.user_id)
                .first()
            )

        u_name = (
            f"{user_data.first_name} {user_data.last_name}"
            if user_data
            else p.user_name
        )
        u_image = (
            user_data.profile_image
            if (user_data and user_data.profile_image)
            else p.user_image
        )

        output.append(
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "post_image": f"{base_url}/{p.post_image}" if p.post_image else None,
                "user_id": p.user_id,
                "user_name": u_name,
                "account_type": p.user_type,  # يتم جلبه من حقل user_type في جدول posts
                "user_image": u_image,
                "create_at": (
                    p.create_at.strftime("%Y-%m-%d %H:%M") if p.create_at else "Not set"
                ),
            }
        )

    return output


@router.get("/all-posts")
async def get_all_posts(db: Session = Depends(get_db)):
    # جلب كل المنشورات أولاً
    all_posts = db.query(models.PostDB).order_by(models.PostDB.id.desc()).all()

    output = []
    for post in all_posts:
        user_name = "User"
        user_image = None

        # جلب بيانات الناشر بناءً على نوعه
        if post.user_type == "jobseeker":
            user = (
                db.query(models.JobSeekerDB)
                .filter(models.JobSeekerDB.id == post.user_id)
                .first()
            )
            if user:
                user_name = f"{user.first_name} {user.last_name}"
                user_image = user.profile_image
        else:
            user = (
                db.query(models.ManagerDB)
                .filter(models.ManagerDB.id == post.user_id)
                .first()
            )
            if user:
                user_name = user.company_name or f"{user.first_name} {user.last_name}"
                user_image = user.profile_image

        output.append(
            {
                "id": post.id,
                "user_id": post.user_id,
                "user_name": user_name,  # تأكدي أن هذا الاسم يطابق الـ Model في الفلاتر
                "user_image": user_image,
                "title": post.title,
                "content": post.content,
                "post_image": post.post_image,
                "time": (
                    post.create_at.strftime("%Y-%m-%d %H:%M")
                    if post.create_at
                    else "Just now"
                ),
                "account_type": post.user_type,
            }
        )
    return output


@router.delete("/delete-post/{post_id}")
async def delete_post(post_id: int, user_id: int, db: Session = Depends(get_db)):
    post = (
        db.query(models.PostDB)
        .filter(models.PostDB.id == post_id, models.PostDB.user_id == user_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Unauthorized or post not found")

    if post.post_image and os.path.exists(post.post_image):
        os.remove(post.post_image)

    db.delete(post)
    db.commit()
    return {"status": "success"}
