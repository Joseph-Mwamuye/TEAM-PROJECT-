from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    title: str
    price: float
    currency: str
    description: Optional[str] = ""
    source: str
    url: HttpUrl

class ProductCreate(ProductBase):
    price_usd: Optional[float] = None
    price_kes: Optional[float] = None

class ProductReponse(ProductBase):
    id: int
    price_usd: Optional[float] = None
    price_kes: Optional[float] = None
    search_id: int
    created_at: datetime

    class Config:
        from_attributes = True




class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=100)


class SearchResponse(BaseModel):
    query: str
    timestamp: datetime
    products: List[ProductReponse]

    class Config:
        from_attributes = True