from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ExpenseCategory(str, Enum):
    Food = "Food"
    Transport = "Transport"
    Shopping = "Shopping"
    Bills = "Bills"
    Entertainment = "Entertainment"
    Health = "Health"
    Other = "Other"

class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    amount: float = Field(..., gt=0)
    category: ExpenseCategory

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: ExpenseCategory
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True