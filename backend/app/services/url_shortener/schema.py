from pydantic import BaseModel


class ShortenResponse(BaseModel):
    short_url: str
    code: str
