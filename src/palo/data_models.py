from typing import Optional, Tuple
from pydantic import BaseModel


class User(BaseModel):
    username: str
    hive: str
    level_name: Optional[str]
    badge_names: Optional[Tuple[str, ...]]
