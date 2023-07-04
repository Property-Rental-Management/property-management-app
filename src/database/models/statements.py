from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Statement(BaseModel):
    """
    Represents a statement.

    Attributes:
    - statement_id (str): The unique ID of the statement.
    - tenant_id (str): The ID of the tenant associated with the statement.
    - month (str): The month of the statement.
    - rental_amount (float): The rental_amount of the statement.
    - items (list[str]): A list of items included in the statement.
    - is_paid (bool): Indicates if the statement has been paid.
    - payment_date (date): The date of payment.
    - generated_at (date): The date when the statement was generated.
    """

    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                              description="The unique ID of the statement.")
    tenant_id: str
    month: str
    amount: float
    items: list[str]
    is_paid: bool
    payment_date: datetime
    generated_at: datetime = Field(default_factory=datetime.now, description="The date when the statement was generated.")
