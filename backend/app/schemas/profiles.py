from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class ProfileCreateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    wallet_address: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    preferred_genres: List[str] = Field(default_factory=list)
    preferred_artists: List[str] = Field(default_factory=list)
    external_auth_id: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    wallet_address: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    preferred_genres: Optional[List[str]] = None
    preferred_artists: Optional[List[str]] = None


class ProfileOut(BaseModel):
    id: str
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    wallet_address: Optional[str] = None
    created_at: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    preferred_genres: List[str] = Field(default_factory=list)
    preferred_artists: List[str] = Field(default_factory=list)
    fan_points: int = 0
    following_count: int = 0
    follower_count: int = 0
    last_active_at: Optional[str] = None