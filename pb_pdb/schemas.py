"""Pydantic's models."""
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime


class Product(BaseModel):
    trello_card_id: str
    trello_link: str
    title: str
    description: str
    category: str
    parrent_id: Optional[str]


class TrelloProduct(BaseModel):
    name: str


class Employee(BaseModel):
    full_name: str
    trello_id: str
    user_pick: Optional[bytes]


class ProductInPage(BaseModel):
    ident: int
    title: str
    designer_name: str
    category: str
    trello_link: str
    start_date: date
    end_production_date: Optional[date]
    is_big: bool = False
    adobe_count: int = 0


class Designer(BaseModel):
    ident: int
    name: str


class Category(BaseModel):
    ident: int
    name: str


class ProductPage(BaseModel):
    products: list[ProductInPage] = []
    page: int = 1
    number_pages: int = 1
    number_products: int = 0
    number_big_products: int = 0
    total_adobe_count: int = 0


class ProductPageData(BaseModel):
    designers: list[Designer] = []
    categories: list[Category] = []


class FilterPage(BaseModel):
    page: int = 1
    designer_id: Optional[int]
    category_id: Optional[int]
    end_design_date_start: Optional[date]
    end_design_date_end: Optional[date]


class UploadProduct(BaseModel):
    prefix: str
    product_file_name: str
    title: str
    slug: str
    excerpt: Optional[str]
    size: str
    description: str
    date_upload: datetime
    schedule_date: Optional[datetime]
    guest_author: Optional[str]
    guest_author_link: Optional[str]
    categories: list[str] = []
    formats: list[str] = []
    tags: list[str] = []


class UploadFreebie(UploadProduct):
    download_by_email: bool = False
    meta_title: Optional[str]
    meta_description: Optional[str]

    @validator('meta_title', pre=True, always=True)
    def template_meta_title(cls, v, values, **kwargs):
        return f'Download {values["title"]}'
    
    @validator('meta_description', pre=True, always=True)
    def template_meta_description(cls, v, values, **kwargs):
        return values['excerpt']


class UploadPlus(UploadProduct):
    meta_title: Optional[str]
    meta_description: Optional[str]

    @validator('meta_title', pre=True, always=True)
    def template_meta_title(cls, v, values, **kwargs):
        return values["title"]
    
    @validator('meta_description', pre=True, always=True)
    def template_meta_description(cls, v, values, **kwargs):
        return values['excerpt']


class UploadPrem(UploadProduct):
    standart_price: int
    extended_price: int
    sale_standart_price: Optional[int]
    sale_extended_price: Optional[int]
    compatibilities: list[str] = []
    meta_title: Optional[str]
    meta_description: Optional[str]

    @validator('meta_title', pre=True, always=True)
    def template_meta_title(cls, v, values, **kwargs):
        return f'Download {values["title"]}'
    
    @validator('meta_description', pre=True, always=True)
    def template_meta_description(cls, v, values, **kwargs):
        return values['excerpt']


class ProductFiles(BaseModel):
    product_url: str
    product_s3_url: Optional[str]
    main_img_url: Optional[str]
    main_img_x2_url: str
    gallery_urls: Optional[str]
    gallery_x2_urls: list[str]
    thumbnail_url: Optional[str]
    thumbnail_x2_url: str
    push_url: Optional[str]
    prem_thumbnail_url: Optional[str]
    prem_thumbnail_x2_url: Optional[str]


class UploaderResponse(BaseModel):
    success: bool
    is_s3: bool
    local_link: str
    s3_link: Optional[str]

class ScheduleUpdate(BaseModel):
    date_time: datetime

class ProductsSchedule(ScheduleUpdate):
    ident: int
    name: str
    edit_link: str

class PageProductsSchedule(BaseModel):
    page: list[ProductsSchedule] = []
