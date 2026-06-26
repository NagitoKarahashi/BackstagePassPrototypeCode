from pydantic import BaseModel, Field

class CreateOrderRequest(BaseModel):
    event_id: str
    quantity: int = Field(ge=1)