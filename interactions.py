from argparse import Action

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from models import FollowDB, JobSeekerDB, ManagerDB, PostDB, SavedPostDB, get_db
from sqlalchemy import and_
from sqlalchemy import text


router = APIRouter(prefix="/interact", tags=["Interactions"])


# 1. دالة الإعجاب (Like/Unlike)
@router.post("/like/{post_id}")
async def toggle_like(post_id: int, user_id: int, db: Session = Depends(get_db)):
    # 1. جلب المنشور
    post = db.query(models.PostDB).filter(models.PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    # 2. التحقق: هل المستخدم مسوي لايك سابقاً؟
    existing_like = (
        db.query(models.LikeDB)
        .filter(models.LikeDB.post_id == post_id, models.LikeDB.user_id == user_id)
        .first()
    )

    if existing_like:
        # ❌ المستخدم مسوي لايك -> نحذفه (إلغاء الإعجاب)
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        action = "unliked"
    else:
        # ✅ المستخدم مو مسوي لايك -> نضيفه (إعجاب جديد)
        new_like = models.LikeDB(post_id=post_id, user_id=user_id)
        db.add(new_like)
        post.likes_count += 1
        action = "liked"

    db.commit()
    return {"status": "success", "action": action, "likes_count": post.likes_count}


# 2. دالة إضافة تعليق
# 1. دالة إضافة تعليق
@router.post("/comment")
async def add_comment(
    post_id: int,
    user_id: int,
    user_name: str,  # أضفنا هذن المعطيات لأنها موجودة بجدولج
    user_image: str,
    content: str,  # بجدولج اسمه content وليس text
    db: Session = Depends(get_db),
):
    # التأكد من وجود المنشور لزيادة العداد
    post = db.query(models.PostDB).filter(models.PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    new_comment = models.CommentDB(
        post_id=post_id,
        user_id=user_id,
        user_name=user_name,
        user_image=user_image,
        content=content,
    )
    db.add(new_comment)

    # تحديث العداد في جدول المنشورات
    post.comments_count += 1

    db.commit()
    return {"status": "success", "message": "تم إضافة التعليق"}


# 2. دالة جلب التعليقات
@router.get("/comments/{post_id}")
async def get_post_comments(post_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(models.CommentDB).filter(models.CommentDB.post_id == post_id).all()
    )
    return comments  # سيعيد كل البيانات (الاسم، الصورة، المحتوى) تلقائياً


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = (
        db.query(models.CommentDB).filter(models.CommentDB.id == comment_id).first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")

    # تنقيص عداد التعليقات من البوست
    post = db.query(models.PostDB).filter(models.PostDB.id == comment.post_id).first()
    if post:
        post.comments_count = max(0, post.comments_count - 1)

    db.delete(comment)
    db.commit()
    return {"status": "success", "message": "تم حذف التعليق"}


# 1. تبديل حالة الحفظ (حفظ / إلغاء حفظ)
@router.post("/save/{post_id}")
async def toggle_save_post(post_id: int, user_id: int, db: Session = Depends(get_db)):
    post = db.query(models.PostDB).filter(models.PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    existing_save = (
        db.query(models.SavedPostDB)
        .filter(
            models.SavedPostDB.post_id == post_id, models.SavedPostDB.user_id == user_id
        )
        .first()
    )

    if existing_save:
        db.delete(existing_save)
        db.commit()
        return {"status": "success", "message": "Removed from saved", "is_saved": False}
    else:
        new_save = models.SavedPostDB(post_id=post_id, user_id=user_id)
        db.add(new_save)
        db.commit()
        return {
            "status": "success",
            "message": "Post saved successfully",
            "is_saved": True,
        }


# 2. جلب قائمة المحفوظات (تأكدي من وجود هذه الدالة لكي لا يظهر Unknown)
@router.get("/saved/{user_id}")
async def get_saved_posts(user_id: int, db: Session = Depends(get_db)):
    saved_items = (
        db.query(models.PostDB)
        .join(models.SavedPostDB, models.PostDB.id == models.SavedPostDB.post_id)
        .filter(models.SavedPostDB.user_id == user_id)
        .all()
    )

    result = []
    for post in saved_items:
        # جلب بيانات صاحب المنشور لكي نتمكن من فتح بروفايله
        owner_type = post.user_type  # 'manager' أو 'jobseeker'

        result.append(
            {
                "id": post.id,
                "title": post.title,
                "location": post.location,
                "post_image": post.post_image,
                # نرسل بيانات المالك هنا
                "owner_id": post.user_id,
                "owner_type": owner_type,
                "user_name": post.user_name,  # اسم صاحب المنشور
            }
        )
    return result  # سيعيد قائمة المنشورات كاملة (العنوان، الموقع، إلخ)


# 3. حذف منشور محدد من المحفوظات (لزر السلة الأحمر)
@router.delete("/saved/remove")
async def remove_saved_post(user_id: int, post_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(models.SavedPostDB)
        .filter(
            models.SavedPostDB.user_id == user_id, models.SavedPostDB.post_id == post_id
        )
        .first()
    )

    if item:
        db.delete(item)
        db.commit()
        return {"status": "success", "message": "Removed from saved items"}

    raise HTTPException(status_code=404, detail="Item not found")


# 1. دالة جلب المتابعين (Followers)
# 1. دالة جلب المتابعين (Followers) المحدثة
@router.get("/followers/{user_id}")
def get_followers(user_id: int, account_type: str, db: Session = Depends(get_db)):
    # الفلترة بالآيدي والنوع معاً لضمان عدم الخلط بين الحسابات
    follows = (
        db.query(models.FollowDB)
        .filter(
            models.FollowDB.following_id == user_id,
            models.FollowDB.following_type == account_type,
        )
        .all()
    )

    if not follows:
        return []

    results = []
    for f in follows:
        fid = f.follower_id
        ftype = f.follower_type

        # جلب بيانات الشخص الذي قام بالمتابعة بناءً على نوع حسابه
        user = (
            db.query(models.ManagerDB).get(fid)
            if ftype == "manager"
            else db.query(models.JobSeekerDB).get(fid)
        )

        if user:
            results.append(
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "type": ftype,
                    "display_info": getattr(
                        user, "company_name", getattr(user, "job_title", "N/A")
                    ),
                    "profile_image": user.profile_image,
                }
            )
    return results


# 2. دالة جلب الذين أتابعهم (Following) المحدثة
@router.get("/following/{user_id}")
def get_following(user_id: int, account_type: str, db: Session = Depends(get_db)):
    # الفلترة بالآيدي والنوع للشخص "المتابع" (أنا)
    follows = (
        db.query(models.FollowDB)
        .filter(
            models.FollowDB.follower_id == user_id,
            models.FollowDB.follower_type == account_type,
        )
        .all()
    )

    if not follows:
        return []

    results = []
    for f in follows:
        fid = f.following_id
        ftype = f.following_type

        # جلب بيانات الشخص الذي أتابعه بناءً على نوع حسابه
        user = (
            db.query(models.ManagerDB).get(fid)
            if ftype == "manager"
            else db.query(models.JobSeekerDB).get(fid)
        )

        if user:
            results.append(
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "type": ftype,
                    "display_info": getattr(
                        user, "company_name", getattr(user, "job_title", "N/A")
                    ),
                    "profile_image": user.profile_image,
                }
            )
    return results


@router.post("/follow")
async def toggle_follow(
    my_id: int,
    my_type: str,
    peer_id: int,
    peer_type: str,
    db: Session = Depends(get_db),
):
    print(f"\n📥 [PYTHON DEBUG]: Incoming Follow Request")
    print(f"   From: ID={my_id}, Type={my_type}")
    print(f"   To:   ID={peer_id}, Type={peer_type}")
    # الضمان الحقيقي: البحث بالآيدي والنوع معاً لمنع التداخل
    existing = (
        db.query(models.FollowDB)
        .filter(
            models.FollowDB.follower_id == my_id,
            models.FollowDB.follower_type == my_type,
            models.FollowDB.following_id == peer_id,
            models.FollowDB.following_type == peer_type,
        )
        .first()
    )

    # جلب الكائنات لتحديث العدادات
    peer = (
        db.query(models.ManagerDB).get(peer_id)
        if peer_type == "manager"
        else db.query(models.JobSeekerDB).get(peer_id)
    )
    me = (
        db.query(models.ManagerDB).get(my_id)
        if my_type == "manager"
        else db.query(models.JobSeekerDB).get(my_id)
    )

    if not peer or not me:
        raise HTTPException(status_code=404, detail="User not found")

    if existing:
        db.delete(existing)
        peer.followers_count = max(0, (peer.followers_count or 0) - 1)
        me.following_count = max(0, (me.following_count or 0) - 1)
        status = False
    else:
        new_follow = models.FollowDB(
            follower_id=my_id,
            follower_type=my_type,
            following_id=peer_id,
            following_type=peer_type,
        )
        db.add(new_follow)
        peer.followers_count = (peer.followers_count or 0) + 1
        me.following_count = (me.following_count or 0) + 1
        status = True

    db.commit()
    return {
        "is_followed": status,
        "followers_count": peer.followers_count,
        "following_count": me.following_count,
    }
