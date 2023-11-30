"""Pydantic's models."""
from pydantic import BaseModel, computed_field
from typing import Optional
from datetime import date, datetime
from pb_admin import schemas as pb_schemas


class Product(BaseModel):
    trello_card_id: str
    trello_link: str
    title: str
    description: str
    category: str
    parrent_id: Optional[str] = None


class TrelloProduct(BaseModel):
    name: str


class Employee(BaseModel):
    full_name: str
    trello_id: str
    user_pick: Optional[bytes] = None


class ProductInPage(BaseModel):
    ident: int
    title: str
    designer_name: str
    category: str
    trello_link: str
    start_date: date
    end_production_date: Optional[date] = None
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
    designer_id: Optional[int] = None
    category_id: Optional[int] = None
    end_design_date_start: Optional[date] = None
    end_design_date_end: Optional[date] = None


class UploadProduct(BaseModel):
    prefix: str
    product_file_name: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    size: str
    description: str
    date_upload: datetime
    schedule_date: Optional[datetime] = None
    guest_author: Optional[str] = None
    guest_author_link: Optional[str] = None
    categories: list[str] = []
    formats: list[str] = []
    tags: list[str] = []


class UploadFreebie(UploadProduct):
    download_by_email: bool = False

    @computed_field
    @property
    def meta_title(self) -> str:
        return f'Download {self.title}'

    @computed_field
    @property
    def meta_description(self) -> str:
        return self.excerpt


class UploadPlus(UploadProduct):

    @computed_field
    @property
    def meta_title(self) -> str:
        return self.title

    @computed_field
    @property
    def meta_description(self) -> str:
        return self.excerpt


class UploadPrem(UploadProduct):
    standart_price: int
    extended_price: int
    sale_standart_price: Optional[int] = None
    sale_extended_price: Optional[int] = None
    compatibilities: list[str] = []

    @computed_field
    @property
    def meta_title(self) -> str:
        return f'Download {self.title}'

    @computed_field
    @property
    def meta_description(self) -> str:
        return self.excerpt


class ProductFiles(BaseModel):
    product_url: str
    product_s3_url: Optional[str] = None
    main_img_url: Optional[str] = None
    main_img_x2_url: str
    gallery_urls: Optional[str] = None
    gallery_x2_urls: list[str]
    thumbnail_url: Optional[str] = None
    thumbnail_x2_url: str
    push_url: Optional[str] = None
    prem_thumbnail_url: Optional[str] = None
    prem_thumbnail_x2_url: Optional[str] = None


class UploaderResponse(BaseModel):
    success: bool
    is_s3: bool
    local_link: str
    s3_link: Optional[str] = None

class ScheduleUpdate(BaseModel):
    date_time: datetime

class ProductsSchedule(ScheduleUpdate):
    ident: int
    name: str
    edit_link: str


class PageProductsSchedule(BaseModel):
    page: list[ProductsSchedule] = []


class BulkTag(BaseModel):
    tag: str
    products: list[pb_schemas.Product]
    category_id: int
    db_id: Optional[int] = None
