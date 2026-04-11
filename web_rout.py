from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from sqlalchemy import or_
from passlib.context import CryptContext
import sys
import sqlite3

from database import get_db
from models import Application, Notification, User, Post, Message
from schemas import (
    ForgotPasswordRequest,
    LoginSchema,
    MessageSchema,
    VerifyOtpRequest,
    ResetPasswordRequest,
    RegisterSchema,
)
import random
import string
import shutil

# import fitz  # PyMuPDF لقراءة ملفات PDF
from utils import extract_text_from_pdf
from fastapi import UploadFile, File

router = APIRouter()

# مسار مجلد الواجهات
FRONTEND_DIR = "frontend"
# 1. إعدادات التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return pwd_context.hash(password[:72])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# 1. دالة عرض الصفحة الرئيسية
@router.get("/")
async def serve_home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def generate_otp():
    return "".join(random.choices(string.digits, k=4))


@router.post("/auth/forgot-password")
async def handle_forgot_password(
    data: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()

    if user:
        otp = generate_otp()
        user.reset_code = otp  # حفظ الرمز في قاعدة البيانات
        db.commit()

        print(f" OTP لـ {user.email} هو: {otp},flush=True")
        # sys.stdout.flush()

        return {"status": "success", "message": "تم إرسال الرمز (راجع الـ Terminal)"}

    return {"status": "error", "message": "الإيميل غير مسجل"}


@router.post("/auth/verify-otp")
async def verify_otp(data: VerifyOtpRequest, db: Session = Depends(get_db)):
    # نبحث عن المستخدم بالإيميل والرمز اللي خزنّاه في الخطوة السابقة
    user = (
        db.query(User)
        .filter(User.email == data.email, User.reset_code == data.otp_code)
        .first()
    )

    if not user:
        raise HTTPException(status_code=400, detail="الرمز غير صحيح")

    # إذا الرمز صح، نمسحه من القاعدة حتى لا يُستخدم مرة ثانية (للأمان)
    user.reset_code = None
    db.commit()

    return {"message": "Success"}


@router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    # البحث عن المستخدم
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # تحديث كلمة السر
    new_hashed_password = get_password_hash(data.new_password)
    user.password = new_hashed_password
    db.commit()

    return {"status": "success", "message": "Password updated successfully"}


UPLOAD_DIR = "static/uploads"  # مجلد الرفع
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/auth/add-test-users")
async def add_test_users(db: Session = Depends(get_db)):
    # إضافة بيانات تجريبية للاختبار
    test_users = [
        {
            "full_name": "أحمد محمد",
            "email": "ahmed@test.com",
            "password": get_password_hash("123456"),
            "role": "seeker",
            "info": "مطور Flutter | مطور تطبيقات موبايل",
            "city": "بغداد",
            "cv_text": "خبرة في Flutter و Dart",
        },
        {
            "full_name": "فاطمة علي",
            "email": "fatima@test.com",
            "password": get_password_hash("123456"),
            "role": "seeker",
            "info": "مصمم UI/UX | مصمم واجهات مستخدم",
            "city": "البصرة",
            "cv_text": "خبرة في Figma و Adobe XD",
        },
        {
            "full_name": "شركة ABC",
            "email": "abc@test.com",
            "password": get_password_hash("123456"),
            "role": "employer",
            "info": "شركة تقنية | 50 موظف",
            "city": "أربيل",
        },
    ]

    for user_data in test_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            new_user = User(**user_data)
            db.add(new_user)

    db.commit()
    return {"message": "تم إضافة البيانات التجريبية"}


@router.post("/auth/upload-cv/{user_id}")
async def upload_cv(
    user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # التأكد من أن الملف هو PDF فقط
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="يرجى رفع ملف بصيغة PDF فقط")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # تكوين اسم الملف الفريد
    filename = f"cv_{user_id}.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # حفظ الملف في السيرفر
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # استخراج النص من PDF (استدعاء الدالة من utils)
    text_content = extract_text_from_pdf(file_path)

    # تحديث قاعدة البيانات
    user.cv_path = filename
    user.cv_text = text_content
    db.commit()

    return {"status": "success", "message": "تم رفع السيرة الذاتية بنجاح"}


@router.get("/auth/search-candidates")
def search_candidates(
    query: str = "",
    city: str = "",
    role: str = "jobseeker",
    db: Session = Depends(get_db),
):
    # نبدأ ببناء الاستعلام الأساسي - نبحث حسب الرول المحدد
    search_query = db.query(User).filter(User.role == role)

    # الفلترة بناءً على الاسم أو المعلومات (المهارات)
    if query:
        search_query = search_query.filter(
            or_(
                User.full_name.contains(query),  # استخدم full_name بدلاً من name
                User.info.contains(query),  # هنا نفترض أن المهارات مخزنة في حقل info
                User.cv_text.contains(query),  # البحث في نص السيرة الذاتية
            )
        )

    # الفلترة بناءً على المدينة إذا تم اختيارها
    if city:
        search_query = search_query.filter(User.city == city)

    results = search_query.all()

    # تحويل النتائج إلى تنسيق JSON متوافق مع الفرونت إند
    output = []
    for user in results:
        output.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "info": user.info,
                "cv_path": user.cv_path,
                "profile_image": user.profile_image,
                "city": user.city,
            }
        )

    return output


@router.post("/auth/register")
async def register_user(data: RegisterSchema, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="الإيميل مسجل مسبقاً")
        new_user = User(
            full_name=data.full_name,
            email=data.email,
            password=get_password_hash(data.password),
            role=data.role,
            info=data.info,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "status": "success",
            "user_id": new_user.id,
            "role": new_user.role,
            "full_name": new_user.full_name,
            "message": "تم إنشاء الحساب بنجاح",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Registration Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في الخادم: {str(e)}")


@router.post("/auth/login")
async def login_user(data: LoginSchema, db: Session = Depends(get_db)):
    user = (
        db.query(User).filter(User.email == data.email, User.role == data.role).first()
    )
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="خطأ في الإيميل أو كلمة المرور")
    return {
        "message": "success",
        "user_id": user.id,
        "role": user.role,
        "full_name": user.full_name,
    }


@router.get("/auth/user/{user_id}")
async def get_user_data(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "info": user.info,
        "role": user.role,
        "profile_image": user.profile_image,
        "cv_path": user.cv_path,
        "city": user.city,
    }


# 2. دالة تحديث بيانات البروفايل
@router.put("/auth/update-profile/{user_id}")
async def update_profile(user_id: int, data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # تحديث البيانات بناءً على ما أرسله المستخدم من الجافا سكريبت
    if "full_name" in data:
        user.full_name = data["full_name"]

    if "info" in data:
        user.info = data["info"]  # خزن النبذة والعنوان الوظيفي هنا

    if "city" in data:
        user.city = data["city"]

    if "password" in data and data["password"]:
        # نستخدم الدالة مالتج حتى نشفر الرمز الجديد قبل الحفظ
        user.password = get_password_hash(data["password"])

    try:
        db.commit()
        return {"status": "success", "message": "تم تحديث البيانات بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="فشل الحفظ في قاعدة البيانات")


@router.post("/auth/upload-avatar/{user_id}")
async def upload_avatar(
    user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # تكوين اسم فريد للملف (مثلاً: avatar_5.jpg)
    extension = os.path.splitext(file.filename)[1]
    filename = f"avatar_{user_id}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # حفظ الملف في السيرفر
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # تحديث قاعدة البيانات بمسار الصورة الجديد
    user.profile_image = f"/{UPLOAD_DIR}/{filename}"
    db.commit()

    return {"status": "success", "image_url": user.profile_image}


@router.post("/auth/create-post")
async def create_post(
    title: str = Form(...),
    description: str = Form(...),
    job_type: str = Form(...),
    location: str = Form(...),
    salary: str = Form(None),
    user_id: int = Form(...),
    user_role: str = Form(...),
    file: UploadFile = File(None),  # الصورة اختيارية
    db: Session = Depends(get_db),
):
    file_path = None

    # إذا المستخدم رفع صورة، نحفظها بالمجلد
    if file:
        extension = os.path.splitext(file.filename)[1]
        # نسمي الصورة باسم فريد (مثلاً الوقت الحالي + اسم الملف) حتى لا تتكرر
        filename = f"post_{datetime.now().timestamp()}{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # الرابط اللي ينخزن بقاعدة البيانات
        file_path = f"/{UPLOAD_DIR}/{filename}"

    # إنشاء المنشور في قاعدة البيانات
    new_post = Post(
        title=title,
        description=description,
        job_type=job_type,
        location=location,
        salary=salary,
        user_id=user_id,
        user_role=user_role,
        image_url=file_path,  # تخزين مسار الصورة هنا ✅
    )
    db.add(new_post)
    db.commit()
    return {"status": "success", "image_url": file_path}


# دالة جلب كل المنشورات من قاعدة البيانات
@router.get("/auth/get-posts")
async def get_posts(db: Session = Depends(get_db)):
    try:
        # جلب المنشورات وترتيبها من الأحدث للأقدم
        posts = db.query(Post).order_by(Post.created_at.desc()).all()

        # تحويل البيانات إلى قائمة (List) حتى يفهمها الجافا سكريبت
        return [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "job_type": p.job_type,
                "location": p.location,
                "salary": p.salary,
                "user_id": p.user_id,
                "user_role": p.user_role,
                "image_url": p.image_url,  # إضافة رابط الصورة في الرد
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# دالة الحذف (Delete)
@router.delete("/auth/delete-post/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    db.delete(post)
    db.commit()
    return {"status": "success", "message": "تم الحذف"}


# دالة التعديل (Update)
@router.put("/auth/edit-post/{post_id}")
async def edit_post(post_id: int, data: dict, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    post.title = data.get("title", post.title)
    post.description = data.get("description", post.description)

    db.commit()
    return {"status": "success", "message": "تم التعديل"}


@router.post("/auth/webapply-job")
async def apply_to_job(data: dict, db: Session = Depends(get_db)):
    post_id = data.get("job_id")
    seeker_id = data.get("jobseeker_id")
    seeker_name = data.get("seeker_name")

    # جلب المنشور لمعرفة صاحبه
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")

    # إضافة الطلب مع التأكد من وجود صاحب العمل
    new_app = Application(post_id=post_id, seeker_id=seeker_id, seeker_name=seeker_name)
    db.add(new_app)

    # إضافة إشعار لصاحب العمل
    new_notification = Notification(
        user_id=post.user_id,  # صاحب الشركة
        title="طلب تقديم جديد",
        message=f"قدم {seeker_name} على وظيفة {post.title}",
    )
    db.add(new_notification)

    db.commit()
    return {"status": "success"}


@router.get("/auth/apps/get-webapplicants/{owner_id}")
async def get_applicants(owner_id: int, db: Session = Depends(get_db)):
    # نجلب الطلبات المرتبطة بمنشورات يملكها هذا الـ owner_id
    results = (
        db.query(Application)
        .join(Post, Application.post_id == Post.id)
        .filter(Post.user_id == owner_id)
        .all()
    )

    output = []
    for app in results:
        # نجلب بيانات الباحث لكل طلب بشكل منفصل لضمان عدم ضياع البيانات
        user = db.query(User).filter(User.id == app.seeker_id).first()
        post = db.query(Post).filter(Post.id == app.post_id).first()

        output.append(
            {
                "seeker_id": app.seeker_id,
                "seeker_name": app.seeker_name
                or (user.full_name if user else "مستخدم"),
                "seeker_email": user.email if user else "لا يوجد",
                "job_title": post.title if post else "وظيفة محذوفة",
                "status": app.status,
                "cv_file": user.cv_path if user else None,
                "cv_content": user.cv_text if user else "",
            }
        )
    return output


@router.put("/auth/apps/update-status/{app_id}")
async def update_application_status(
    app_id: int, data: dict, db: Session = Depends(get_db)
):
    new_status = data.get("status")  # مقبول أو مرفوض

    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    application.status = new_status

    # إرسال إشعار للباحث عن عمل بتحديث حالة طلبه
    new_notification = Notification(
        user_id=application.seeker_id,
        title="تحديث في حالة الطلب",
        message=(
            f"تمت الموافقة على طلبك" if new_status == "مقبول" else f"للأسف تم رفض طلبك"
        ),
    )

    db.add(new_notification)
    db.commit()
    return {"status": "success", "message": f"تم التحديث إلى {new_status}"}


@router.post("/auth/send-message")
def send_message(msg: MessageSchema, db: Session = Depends(get_db)):
    try:
        new_msg = Message(
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            sender_type=msg.sender_type,
            content=msg.content,
            message_text=msg.message_text or "",  # التأكد من ملء الحقل
        )
        db.add(new_msg)
        sender_user = db.query(User).filter(User.id == msg.sender_id).first()
        sender_name = sender_user.full_name if sender_user else "مستخدم مجهول"

        new_notification = Notification(
            user_id=msg.receiver_id,
            title="رسالة جديدة",
            message=f"لديك رسالة جديدة من مستخدم {msg.sender_type} اسمه {sender_name}",
        )
        db.add(new_notification)
        db.commit()

        return {"status": "success"}
    except Exception as e:
        print(f"Error in send_message: {e}")
        return {"status": "error"}


# 2. جلب المحادثة
@router.get("/auth/get-chat/{u1}/{u2}")
def get_chat(u1: int, u2: int, db: Session = Depends(get_db)):
    return (
        db.query(Message)
        .filter(
            ((Message.sender_id == u1) & (Message.receiver_id == u2))
            | ((Message.sender_id == u2) & (Message.receiver_id == u1))
        )
        .order_by(Message.created_at.asc())
        .all()
    )


@router.get("/auth/get-users-list")
def get_users_list(db: Session = Depends(get_db)):
    # جلب كل المستخدمين لعرضهم في قائمة الدردشة
    users = db.query(User).all()
    return users


@router.get("/auth/get-chat-users/{user_id}")
def get_chat_users(user_id: int, db: Session = Depends(get_db)):
    # جلب المستخدمين اللي عندهم محادثات مع المستخدم الحالي
    try:
        # ابحث عن جميع المحادثات التي يكون فيها المستخدم الحالي مرسل أو مستقبل
        chat_user_ids = (
            db.query(Message.sender_id, Message.receiver_id)
            .filter((Message.sender_id == user_id) | (Message.receiver_id == user_id))
            .all()
        )

        # استخرج معرفات المستخدمين الفريدة
        unique_ids = set()
        for sender_id, receiver_id in chat_user_ids:
            if sender_id != user_id:
                unique_ids.add(sender_id)
            if receiver_id != user_id:
                unique_ids.add(receiver_id)

        # جلب بيانات المستخدمين
        if unique_ids:
            chat_users = db.query(User).filter(User.id.in_(unique_ids)).all()
        else:
            chat_users = []

        return chat_users
    except Exception as e:
        print(f"Error in get_chat_users: {e}")
        return []


# تحميل/عرض ملف CV
@router.get("/auth/download-cv/{user_id}")
def download_cv(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.cv_path:
        raise HTTPException(status_code=404, detail="لا يوجد CV لهذا المستخدم")

    file_path = os.path.join(UPLOAD_DIR, user.cv_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="الملف غير موجود على السيرفر")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=user.cv_path,
        headers={"Content-Disposition": f"inline; filename={user.cv_path}"},
    )


# حذف ملف CV
@router.delete("/auth/delete-cv/{user_id}")
def delete_cv(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    if not user.cv_path:
        raise HTTPException(status_code=404, detail="لا يوجد CV لحذفه")

    # حذف الملف من السيرفر
    file_path = os.path.join(UPLOAD_DIR, user.cv_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"خطأ في حذف الملف: {e}")

    # حذف البيانات من قاعدة البيانات
    user.cv_path = None
    user.cv_text = None
    db.commit()

    return {"status": "success", "message": "تم حذف السيرة الذاتية بنجاح"}


# 1. دالة جلب الإشعارات الخاصة بمستخدم معين
@router.get("/auth/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    # جلب الإشعارات من الجدول الذي أنشأتِهِ
    return db.query(Notification).filter(Notification.user_id == user_id).all()


@router.put("/auth/notifications/read/{notification_id}")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    notification.is_read = True
    db.commit()
    return {"status": "success", "message": "تم وضع الإشعار كمقروء"}
