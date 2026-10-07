from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class User:
    """User model for MongoDB"""
    
    def __init__(
        self,
        email: str,
        name: str,
        role: Optional[str] = None,
        experience: Optional[int] = None,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        salary: Optional[int] = None,
        preferences: Optional[dict] = None,
        gmail_credentials: Optional[dict] = None,
        created_at: datetime = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id or ObjectId()
        self.email = email
        self.name = name
        self.role = role
        self.experience = experience
        self.skills = skills or []
        self.location = location
        self.salary = salary
        self.preferences = preferences or {}
        self.gmail_credentials = gmail_credentials
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "_id": self._id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "experience": self.experience,
            "skills": self.skills,
            "location": self.location,
            "salary": self.salary,
            "preferences": self.preferences,
            "gmail_credentials": self.gmail_credentials,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
