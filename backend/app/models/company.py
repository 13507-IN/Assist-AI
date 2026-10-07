from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class Company:
    """Company model for MongoDB"""
    
    def __init__(
        self,
        name: str,
        website: Optional[str] = None,
        hiring_signal: str = "unknown",
        summary: Optional[str] = None,
        domain: Optional[str] = None,
        relevance_score: float = 0.0,
        tech_signals: Optional[List[str]] = None,
        outreach_method: Optional[str] = None,
        outreach_instructions: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        last_checked: Optional[datetime] = None,
        created_at: datetime = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id or ObjectId()
        self.name = name
        self.website = website
        self.hiring_signal = hiring_signal  # "active", "inactive", "unknown"
        self.summary = summary
        self.domain = domain
        self.relevance_score = relevance_score
        self.tech_signals = tech_signals or []
        self.outreach_method = outreach_method  # "email", "linkedin", "apply"
        self.outreach_instructions = outreach_instructions
        self.tags = tags or []
        self.source = source
        self.last_checked = last_checked or datetime.utcnow()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "website": self.website,
            "hiring_signal": self.hiring_signal,
            "summary": self.summary,
            "domain": self.domain,
            "relevance_score": self.relevance_score,
            "tech_signals": self.tech_signals,
            "outreach_method": self.outreach_method,
            "outreach_instructions": self.outreach_instructions,
            "tags": self.tags,
            "source": self.source,
            "last_checked": self.last_checked,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
