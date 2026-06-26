from pydantic import BaseModel


class ArtistFollowRequest(BaseModel):
    artist_id: str