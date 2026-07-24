from pydantic import BaseModel,Field,EmailStr
from datetime import datetime,UTC

class userCreate(BaseModel):
    name : str
    email: EmailStr
    password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
class userResponse(BaseModel):
    id: str
    name : str
    email: EmailStr
    created_at: datetime
    updated_at: datetime 
    class Config:
        from_attributes = True

class userLogin(BaseModel):
    email: EmailStr
    password: str

class authMW(BaseModel):
    id : str
    name: str
    email: EmailStr

class QuestionSchema(BaseModel):
    question: str
    thread_id: str | None = None
