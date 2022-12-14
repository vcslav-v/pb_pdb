"""Pydantic's models."""
from pydantic import BaseModel
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

class ProductPage(BaseModel):
    products: list[ProductInPage] = []
    page: int
    number_pages: int