from sqlalchemy import (Boolean, Column, Date, ForeignKey, Integer,
                        LargeBinary, Text, DateTime)
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
    start_date = Column(Date)
    end_date = Column(Date)
    end_production_date = Column(Date)
    description = Column(Text)
    work_directory = Column(Text)
    done = Column(Boolean, default=False)
    dropbox_share_url = Column(Text)
    trello_link = Column(Text)
    is_big_product = Column(Boolean, default=False)
    adobe_count = Column(Integer, default=0)
    is_extra = Column(Boolean, default=False)

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


class UploadStatus(Base):
    '''Market Place Link.'''

    __tablename__ = 'upload_status'

    id = Column(Integer, primary_key=True)
    prefix = Column(Text, unique=True)
    status = Column(Text)


class ProductSchedule(Base):
    '''Product schedule.'''

    __tablename__ = 'product_schedule'

    id = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    edit_url = Column(Text)
    name = Column(Text)


class Callback(Base):
    '''callbacks.'''

    __tablename__ = 'callbacks'

    id = Column(Integer, primary_key=True)
    prefix = Column(Text, unique=True)
    data = Column(Text)


class BulkTagTask(Base):
    '''Bulk tag task.'''

    __tablename__ = 'bulk_tag_task'

    id = Column(Integer, primary_key=True)
    value = Column(Text)
    in_progress = Column(Boolean, default=False)
