from pydantic import BaseModel, Field


class Profile(BaseModel):
    """
        **Profile**
            allows users to create personalized settings
            such us - deposit multiplier

    """
    user_id: str
    deposit_multiplier: float = Field(default="2")
    currency: str = Field(default="R")
