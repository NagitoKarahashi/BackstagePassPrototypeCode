from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.artists_service import (
    follow_artist_service,
    unfollow_artist_service,
    list_followed_artists_service,
)

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("/follows")
def list_followed_artists(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return list_followed_artists_service(sb, current_user.id)


@router.post("/{artist_id}/follow")
def follow_artist(
    artist_id: str,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return follow_artist_service(sb, current_user.id, artist_id)


@router.delete("/{artist_id}/follow")
def unfollow_artist(
    artist_id: str,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return unfollow_artist_service(sb, current_user.id, artist_id)