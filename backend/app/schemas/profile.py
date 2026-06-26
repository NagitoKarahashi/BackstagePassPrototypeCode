from pydantic import BaseModel
from typing import Optional, List

class ProfileResponse(BaseModel):
    id: str
    username: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None