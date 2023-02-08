"""Pydantic's models."""
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date


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
    ident: str
    title: str
    short_description: str
    designer_name: str
    designer_id: int
    category: str
    category_id: int
    trello_link: str
    dropbox_link: str
    children: list['ProductInPage'] = []
    is_done: bool
    start_date: date
    end_date: Optional[date]
    end_designer_date: Optional[date]


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
    number_products: int = 1


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
    excerpt: str
    description: str
    size: str
    guest_author: Optional[str]
    guest_author_link: Optional[str]
    date_upload: date
    categories: list[str] = []
    formats: list[str] = []


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


class ProductFiles(BaseModel):
    product_url: str
    main_img_url: Optional[str]
    main_img_x2_url: str
    gallery_urls: Optional[str]
    gallery_x2_urls: list[str]
    thumbnail_url: Optional[str]
    thumbnail_x2_url: str
    push_url: Optional[str]
