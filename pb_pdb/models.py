from datetime import datetime

from sqlalchemy import (Boolean, Column, Date, ForeignKey, Integer,
                        LargeBinary, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    '''Product.'''

    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    trello_card_id = Column(Text, unique=True)
    readable_uid = Column(Text, unique=True)
    work_title = Column(Text)
    title = Column(Text)
    cover = Column(LargeBinary)
    start_date = Column(Date, default=datetime.utcnow().date())
    description = Column(Text)
    work_directory = Column(Text)
    done = Column(Boolean, default=False)
    dropbox_share_url = Column(Text)

    designer_id = Column(Integer, ForeignKey('employees.id'))
    designer = relationship('Employee')

    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category')

    market_place_links = relationship('MarketPlaceLink', back_populates='product', uselist=False)

    parent_id = Column(Integer, ForeignKey('products.id'))
    parent = relationship('Product', remote_side=[id])

    children = relationship('Product', remote_side=[id], uselist=True)


class Category(Base):
    '''Category.'''

    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    prefix = Column(Text, unique=True)
    number_products_created = Column(Integer, default=0)

    products = relationship('Product', back_populates='category')


class Employee(Base):
    '''Employee.'''

    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    trello_id = Column(Text, unique=True)
    full_name = Column(Text)
    user_pick = Column(LargeBinary)

    products_as_designer = relationship('Product', back_populates='designer')


class MarketPlaceLink(Base):
    '''Market Place Link.'''

    __tablename__ = 'market_place_links'

    id = Column(Integer, primary_key=True)
    pixelbuddha = Column(Text)
    creative_market = Column(Text)
    you_work_for_them = Column(Text)
    yellow_images = Column(Text)
    designcuts = Column(Text)
    elements = Column(Text)
    art_station = Column(Text)
    freepick = Column(Text)
    adobe_stock = Column(Text)
    graphicriver = Column(Text)
    etsy = Column(Text)

    product_id = Column(Integer, ForeignKey('products.id'))
    product = relationship('Product', back_populates='market_place_links')
