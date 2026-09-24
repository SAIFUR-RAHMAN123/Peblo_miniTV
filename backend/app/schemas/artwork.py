from pydantic import BaseModel


class ArtworkOut(BaseModel):
    id: int
    episode_id: int
    kind: str
    storage_key: str
    width: int
    height: int
    size_bytes: int
    url: str

    model_config = {"from_attributes": True}