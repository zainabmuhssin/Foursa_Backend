from pydantic import BaseModel
from typing import Optional


class OtpVerify(BaseModel):
    email: str
    otp_code: str


class ManagerCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    companyName: str
    businessType: str


class JobSeekerCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    job_title: Optional[str] = None
    is_cv_public: Optional[bool] = True
    cv_content: str  # ملف الـ PDF كـ bytes


class EmailRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    sender_type: str  # تأكدي أن هذا السطر موجود
    content: str


class UserRole(BaseModel):
    seeker: str = "jobseeker"
    manager: str = "manager"


class LoginSchema(BaseModel):
    email: str
    password: str
    role: str  # "jobseeker" أو "manager"


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp_code: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str


class RegisterSchema(BaseModel):
    full_name: str
    email: str
    password: str
    role: str  # "jobseeker" أو "manager"
    info: Optional[str] = None  # معلومات إضافية (مثل job_title أو company_name)


class MessageSchema(BaseModel):
    sender_id: int
    receiver_id: int
    sender_type: str  # "jobseeker" أو "manager"
    content: str
    message_text: str = ""  # معرف الرسالة (اختياري، يتم إنشاؤه تلقائيًا)
