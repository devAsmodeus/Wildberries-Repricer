from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, timedelta


class MessageModel(BaseModel):
    API_ID: Optional[int]
    API_HASH: Optional[str]
    SESSION_STRING: Optional[str]
    scriptName: Optional[str]
    startTime: datetime
    runTime: Optional[timedelta]
    users: list[str]
    error: bool
    errorText: Optional[str]
    message: Optional[str]


class CardPriceModel(BaseModel):
    nmID: int
    vendorCode: str
    brand: str
    prices: list[float | int]
    discount: int
    addClubDiscount: int
    clubDiscountedPrices: list[float | int]
    discountOnSite: Optional[int] = 0
    discountedPrices: list[float | int]
    discountSitePrice: Optional[float] = 0.0
    walletSitePrice: Optional[float] = 0.0

    @field_validator('discountOnSite', mode='before')
    @classmethod
    def format_article(cls, value: Optional[int]) -> int:
        return 0 if value is None else value


class CardPriceEditModel(BaseModel):
    price: int
    discount: int
    discountSite: int
    coefficientWallet: float
