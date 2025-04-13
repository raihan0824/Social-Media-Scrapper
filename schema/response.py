from pydantic import BaseModel

class ResponseBody(BaseModel):
    username: str
    content: str
    url: str

class ConversionBody(BaseModel):
    url: str