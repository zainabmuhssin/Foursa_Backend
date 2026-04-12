from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import requests
from pydantic import BaseModel

# 1. إعدادات التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return pwd_context.hash(password[:72])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


router = APIRouter(prefix="/auth", tags=["Authentication"])
