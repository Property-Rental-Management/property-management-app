from pydantic import BaseModel, Field


class Profile(BaseModel):
    """
        **Profile**
            allows users to create personalized settings
            such us - deposit multiplier

    """
    user_id: str
    deposit_multiplier: int = Field(default="2")
    currency: str = Field(default="R")
    tax_rate: int = Field(default=0)

    def __eq__(self, other):
        if not isinstance(other, Profile):
            return False
        return self.user_id == other.user_id
