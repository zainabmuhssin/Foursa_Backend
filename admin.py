from fastapi import APIRouter, Depends
from database import get_db
from models import (
    PostDB,
    User,
    ApplicationDB,
    JobSeekerDB,
    ManagerDB,
    NotificationDB,
    LikeDB,
    CommentDB,
    FollowDB,
    ContactMessage,
    jobDB,
    MessageDB,
    Post,
    Application,
    Message,
    Notification,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard-stats")
def get_stats(db=Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_job_seekers": db.query(JobSeekerDB).count(),
        "total_managers": db.query(ManagerDB).count(),
        "total_posts": db.query(PostDB).count(),
        "total_web_posts": db.query(Post).count(),
        "total_applications": db.query(ApplicationDB).count(),
        "total_web_applications": db.query(Application).count(),
        "total_messages": db.query(MessageDB).count(),
        "total_web_messages": db.query(Message).count(),
        "total_notifications": db.query(NotificationDB).count(),
        "total_web_notifications": db.query(Notification).count(),
        "total_likes": db.query(LikeDB).count(),
        "total_comments": db.query(CommentDB).count(),
        "total_follows": db.query(FollowDB).count(),
        "total_contact_messages": db.query(ContactMessage).count(),
        "total_jobs": db.query(jobDB).count(),
    }


@router.get("/all-users")
def get_all_users(db=Depends(get_db)):
    return db.query(User).all()


@router.get("/all-job-seekers")
def get_all_job_seekers(db=Depends(get_db)):
    return db.query(JobSeekerDB).all()


router.get("/all-managers")


def get_all_managers(db=Depends(get_db)):
    return db.query(ManagerDB).all()


@router.delete("/delete-user/{user_id}/{is_web}")
def delete_user(user_id: int, is_web: bool, db=Depends(get_db)):
    if is_web:
        user = db.query(User).filter(User.id == user_id).first()
    else:
        # هنا تمسحين من جداول التطبيق حسب الـ ID
        user = (
            db.query(JobSeekerDB).filter(JobSeekerDB.id == user_id).first()
            or db.query(ManagerDB).filter(ManagerDB.id == user_id).first()
        )

    if user:
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    return {"error": "User not found"}


# دالة لحذف منشور غير لائق
@router.delete("/delete-post/{post_id}/{is_web}")
def delete_post(post_id: int, is_web: bool, db=Depends(get_db)):
    model = Post if is_web else PostDB
    post = db.query(model).filter(model.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
        return {"message": "Post deleted"}
    return {"error": "Post not found"}