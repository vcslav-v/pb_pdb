"""Pydantic's models."""
from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    trello_card_id: str
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
