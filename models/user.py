from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    name: str
    destination_number: str
    selected: bool
    callStatus: str
    questions: Optional[List[str]] = [] 
    transcript: Optional[str] = "" 
