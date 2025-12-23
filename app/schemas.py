from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SeedUpdate(BaseModel):
    """Schema for validating seed updates from forms."""

    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    packets_made: int = Field(0, ge=0)
    seed_source: Optional[str] = ""
    date_ordered: Optional[date] = None
    date_finished: Optional[date] = None
    date_cataloged: Optional[date] = None
    date_ran_out: Optional[date] = None
    amount_text: Optional[str] = ""

    @field_validator("seed_source", "amount_text")
    @classmethod
    def _strip_optional(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    @field_validator(
        "date_ordered",
        "date_finished",
        "date_cataloged",
        "date_ran_out",
        mode="before",
    )
    @classmethod
    def _empty_str_to_none(cls, value):
        if value in ("", None):
            return None
        return value


class InventoryUpdate(BaseModel):
    """Schema for validating inventory updates from forms."""

    current_amount: Optional[str] = ""
    buy_more: bool = False
    extra: bool = False
    notes: Optional[str] = ""

    @field_validator("current_amount", "notes")
    @classmethod
    def _strip_text(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value
