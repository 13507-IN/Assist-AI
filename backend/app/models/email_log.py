from typing import Optional
from datetime import datetime
from bson import ObjectId


class EmailLog:
    """Email sending log model for MongoDB"""
    
    def __init__(
        self,
        user_id: ObjectId,
        company_id: ObjectId,
        company_name: str,
        recipient_email: str,
        subject: str,
        body: str,
        status: str = "drafted",  # "drafted", "sent", "failed"
        error_message: Optional[str] = None,
        opened: bool = False,
        clicked: bool = False,
        replied: bool = False,
        created_at: datetime = None,
        sent_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id or ObjectId()
        self.user_id = user_id
        self.company_id = company_id
        self.company_name = company_name
        self.recipient_email = recipient_email
        self.subject = subject
        self.body = body
        self.status = status
        self.error_message = error_message
        self.opened = opened
        self.clicked = clicked
        self.replied = replied
        self.created_at = created_at or datetime.utcnow()
        self.sent_at = sent_at
    
    def to_dict(self):
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "recipient_email": self.recipient_email,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "error_message": self.error_message,
            "opened": self.opened,
            "clicked": self.clicked,
            "replied": self.replied,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
        }
