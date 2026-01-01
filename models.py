from pydantic import BaseModel, Field
from typing import List, Optional

# Models
class SpyCat(BaseModel):
    name: str
    years_of_experience: int = Field(ge=0)
    breed: str
    salary: float = Field(gt=0)

class SpyCatResponse(SpyCat):
    id: str

class SpyCatUpdate(BaseModel):
    salary: float = Field(gt=0)

class Target(BaseModel):
    name: str
    country: str
    notes: str = ""
    complete: bool = False

class TargetResponse(Target):
    id: str

class Mission(BaseModel):
    targets: List[Target] = Field(min_items=1, max_items=3)

class MissionResponse(BaseModel):
    id: str
    cat_id: Optional[str] = None
    targets: List[TargetResponse]
    complete: bool

class MissionUpdate(BaseModel):
    notes: Optional[str] = None
    complete: Optional[bool] = None

class AssignCat(BaseModel):
    cat_id: str