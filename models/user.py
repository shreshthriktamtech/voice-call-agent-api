from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    name: str
    phone: str
    call_status: Optional[str] = "pending" 
    instruction: Optional[str] = "" 
    schedule_time: Optional[str] = "" 
    transcription: Optional[str] = "" 
