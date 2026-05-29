from typing import Optional

from pydantic import BaseModel


class MusicModeRequest(BaseModel):
    mode: str


class MusicPlayRequest(BaseModel):
    playlist_url: Optional[str] = None
    mode: Optional[str] = None
    song: Optional[str] = None
    dry_run: bool = False
