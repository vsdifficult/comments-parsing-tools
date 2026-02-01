from pydantic import BaseModel 

class Comment(BaseModel): 
    id: str     
    url: str
    content: str
    likes: int 
    date: str  
    source: str

class CreateComment(BaseModel):
    url: str
    content: str
    likes: int 
    date: str 
    source: str 
    author: str 