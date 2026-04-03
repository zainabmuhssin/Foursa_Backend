from fastapi import APIRouter, Depends, HTTPException, Query  # أضفت Query هنا
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from database import get_db
from models import MessageDB, JobSeekerDB, ManagerDB, NotificationDB
from schemas import MessageCreate
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["Chat"])

BASE_URL = "https://foursa-backend.onrender.com/uploads/"


@router.post("/send_message")
def send_message(msg: MessageCreate, db: Session = Depends(get_db)):
    try:
        # 1. حفظ الرسالة الأصلية
        new_msg = MessageDB(
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            sender_type=msg.sender_type,
            content=msg.content,
        )
        db.add(new_msg)
        db.flush()  # للحصول على ID الرسالة إذا احتجتيه

        # 2. جلب اسم المرسل بدقة لعنوان الإشعار
        sender_name = "مستخدم"
        if msg.sender_type == "jobseeker":
            user = db.query(JobSeekerDB).filter(JobSeekerDB.id == msg.sender_id).first()
        else:
            user = db.query(ManagerDB).filter(ManagerDB.id == msg.sender_id).first()

        if user:
            sender_name = f"{user.first_name} {user.last_name}"

        # 3. تحديد نوع المستلم (عكس نوع المرسل دائماً)
        # إذا المرسل باحث، فالمستلم مدير.. والعكس صحيح
        actual_receiver_type = (
            "manager" if msg.sender_type == "jobseeker" else "jobseeker"
        )

        # 4. إنشاء سجل الإشعار للمستلم الصحيح
        new_notif = NotificationDB(
            user_id=msg.receiver_id,  # آيدي الشخص المستلم
            user_type=actual_receiver_type,  # نوع الشخص المستلم (manager أو jobseeker)
            sender_id=msg.sender_id,  # آيدي الشخص الذي أرسل الرسالة (لكي يفتح الدردشة معه)
            sender_type=msg.sender_type,  # نوع الشخص الذي أرسل الرسالة
            type="message",
            title="رسالة جديدة",
            body=f"لديك رسالة جديدة من {sender_name}",
            is_read=False,
            create_at=datetime.now(),  # تأكدي من استيراد datetime
        )
        db.add(new_notif)

        db.commit()
        return {"status": "success"}

    except Exception as e:
        db.rollback()
        print(f"Error in send_message: {str(e)}")  # للديبيج
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/seeker/{seeker_id}/manager/{manager_id}")
def get_chat_history(seeker_id: int, manager_id: int, db: Session = Depends(get_db)):
    # جلب الرسائل التي لم يتم حذفها من قبل الأطراف المعنية
    messages = (
        db.query(MessageDB)
        .filter(
            or_(
                and_(
                    MessageDB.sender_id == seeker_id,
                    MessageDB.receiver_id == manager_id,
                    MessageDB.deleted_by_sender == False,
                ),
                and_(
                    MessageDB.sender_id == manager_id,
                    MessageDB.receiver_id == seeker_id,
                    MessageDB.deleted_by_receiver == False,
                ),
            )
        )
        .order_by(MessageDB.timestamp.asc())
        .all()
    )
    return messages


@router.get("/list/{my_id}")
def get_chat_list(my_id: int, user_type: str, db: Session = Depends(get_db)):
    # 1. جلب كل الرسائل التي يكون المستخدم طرفاً فيها (مرسل أو مستقبل) ولم يتم حذفها
    messages = (
        db.query(MessageDB)
        .filter(
            or_(
                and_(
                    MessageDB.sender_id == my_id, MessageDB.deleted_by_sender == False
                ),
                and_(
                    MessageDB.receiver_id == my_id,
                    MessageDB.deleted_by_receiver == False,
                ),
            )
        )
        .order_by(MessageDB.timestamp.desc())  # ترتيب تنازلي لجلب أحدث الرسائل أولاً
        .all()
    )

    contacts = {}
    for msg in messages:
        # 2. تحديد من هو الطرف الآخر (Peer) بناءً على حساب المستخدم الحالي
        is_me_sender = msg.sender_id == my_id
        peer_id = msg.receiver_id if is_me_sender else msg.sender_id

        # 3. جلب بيانات الطرف الآخر بناءً على نوع حساب المستخدم الحالي
        # إذا كنتِ (مديرة)، فالطرف الآخر (باحث).. والعكس صحيح
        if user_type == "manager":
            peer_type = "jobseeker"
            user = db.query(JobSeekerDB).filter(JobSeekerDB.id == peer_id).first()
        else:
            peer_type = "manager"
            user = db.query(ManagerDB).filter(ManagerDB.id == peer_id).first()

        if not user:
            continue

        # إنشاء مفتاح فريد لكل محادثة لضمان عدم تكرار الشخص في القائمة
        chat_key = f"{peer_id}_{peer_type}"

        if chat_key not in contacts:
            # 4. استخراج اسم الصورة فقط (بدون رابط كامل)
            p_image = getattr(user, "profile_image", "")

            contacts[chat_key] = {
                "peer_id": peer_id,
                "peer_name": f"{user.first_name} {user.last_name}",
                "peer_image": p_image,  # ✅ نرسل اسم الملف فقط ليتوافق مع كود الدارت عندكِ
                "peer_type": peer_type,
                "unread_count": 0,  # يمكنكِ تطوير نظام عداد الرسائل غير المقروءة لاحقاً
                "last_message": msg.content,
                "time": msg.timestamp.strftime("%I:%M %p"),
            }

    # إرجاع القائمة كـ List مرتبة حسب وقت آخر رسالة
    return list(contacts.values())


@router.delete("/delete/{my_id}/{peer_id}")
def delete_chat(my_id: int, peer_id: int, my_type: str, db: Session = Depends(get_db)):
    try:
        # 1. تحديث الرسائل التي أرسلتها أنا لتصبح محذوفة عندي
        db.query(MessageDB).filter(
            and_(
                MessageDB.sender_id == my_id,
                MessageDB.sender_type == my_type,
                MessageDB.receiver_id == peer_id,
            )
        ).update({"deleted_by_sender": True})

        # 2. تحديث الرسائل التي استلمتها أنا لتصبح محذوفة عندي
        # ملاحظة: نحتاج تخمين نوع الطرف الآخر (peer_type) أو تمريره
        peer_type = "manager" if my_type == "jobseeker" else "jobseeker"
        db.query(MessageDB).filter(
            and_(
                MessageDB.receiver_id == my_id,
                MessageDB.sender_id == peer_id,
                MessageDB.sender_type == peer_type,
            )
        ).update({"deleted_by_receiver": True})

        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
