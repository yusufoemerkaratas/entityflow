from typing import Literal

from pydantic import BaseModel


class EntityReviewRequest(BaseModel):
    review_status: Literal["approved", "rejected"]