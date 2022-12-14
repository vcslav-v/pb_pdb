from datetime import datetime
from math import ceil
from typing import Optional

from pb_pdb import dropbox_tools, models, schemas
from pb_pdb.db import SessionLocal

PRODUCTS_ON_PAGE = 10


def get_exist_category_from_list(labels: list[str]) -> Optional[str]:
    with SessionLocal() as session:
        for label in labels:
            category = session.query(models.Category).filter_by(name=label).first()
            if category:
                return category.name


def add_product(product: schemas.Product, designer: schemas.Employee) -> str:
    with SessionLocal() as session:
        db_designer = session.query(models.Employee).filter_by(trello_id=designer.trello_id).first()
        if not db_designer:
            db_designer = models.Employee(
                trello_id=designer.trello_id,
                full_name=designer.full_name,
                user_pick=designer.user_pick,
            )
            session.add(db_designer)
            session.commit()
        category = session.query(models.Category).filter_by(name=product.category).first()
        db_product = session.query(models.Product).filter_by(
            trello_card_id=product.trello_card_id
        ).first()
        if not db_product:
            db_product = models.Product(trello_card_id=product.trello_card_id)
            db_product.start_date = datetime.utcnow().date()
            session.add(db_product)
        if db_product.category != category:
            category.number_products_created += 1
            db_product.readable_uid = f'{category.prefix}{category.number_products_created}'
        db_product.work_title = product.title
        db_product.description = product.description
        db_product.designer = db_designer
        db_product.category = category
        db_product.trello_link = product.trello_link

        if product.parrent_id:
            db_parrent = session.query(models.Product).filter_by(
                trello_card_id=product.parrent_id
            ).first()
            db_product.parent = db_parrent
            db_product.readable_uid = f'{db_product.readable_uid} ({db_parrent.readable_uid})'

        full_product_name = f'{db_product.readable_uid} - {product.title}'
        db_product.work_directory = dropbox_tools.make_directory(
            product.category,
            product.title,
            full_product_name,
        )
        db_product.dropbox_share_url = dropbox_tools.get_share_link(db_product.work_directory)

        session.commit()

        return full_product_name, db_product.dropbox_share_url


def is_child(card_id: str) -> bool:
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        if db_product:
            return bool(db_product.parent_id)


def make_final_text(card_id: str, card_name: str, title: str, description: str):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        new_path = dropbox_tools.rename(
            db_product.work_directory,
            card_name, 
            title,
            db_product.work_title,
        )
        db_product.title = title
        db_product.description = description
        db_product.work_directory = new_path
        session.commit()


def publish_product(card_id: str):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        db_product.end_date = datetime.utcnow().date()
        db_product.done = True
        session.commit()


def get_products(page: int = 1) -> schemas.ProductPage:
    result = schemas.ProductPage()
    result.page = page
    page_start = PRODUCTS_ON_PAGE * (page - 1)
    page_end = PRODUCTS_ON_PAGE * page
    with SessionLocal() as session:
        all_db_products = session.query(models.Product).filter_by(parent_id=None).count()
        result.number_pages = ceil(all_db_products / PRODUCTS_ON_PAGE)
        db_products = session.query(models.Product).filter_by(
            parent_id=None
        ).order_by(
            models.Product.start_date
        ).all()
        for db_product in db_products:
            result.products.append(schemas.ProductInPage(
                ident = db_product.readable_uid,
                title = db_product.title if db_product.title else db_product.work_title,
                short_description = db_product.description[:20] if db_product.description else '',
                designer_name = db_product.designer.full_name,
                designer_id = db_product.designer.id,
                category = db_product.category.name,
                category_id = db_product.category.id,
                trello_link = db_product.trello_link,
                dropbox_link = db_product.dropbox_share_url,
                is_done = db_product.done,
                start_date=db_product.start_date,
            ))
            if db_product.end_date:
                result.products[-1].end_date = db_product.end_date
            db_products_children = session.query(models.Product).filter_by(parent_id=db_product.id).all()
            for child in db_products_children:
                result.products[-1].children.append(schemas.ProductInPage(
                    ident = child.readable_uid,
                    title = child.title if child.title else child.work_title,
                    short_description = child.description[:20] if child.description else '',
                    designer_name = child.designer.full_name,
                    designer_id = child.designer.id,
                    category = child.category.name,
                    category_id = child.category.id,
                    trello_link = child.trello_link,
                    dropbox_link = child.dropbox_share_url,
                    is_done = child.done,
                    start_date=db_product.start_date,
                ))
                if child.end_date:
                    result.products[-1].children[-1].end_date = child.end_date
    return result

def get_products_done() -> list[str]:
    with SessionLocal() as session:
        db_products = session.query(models.Product).filter_by(done=True).all()
        resutl = []
        for db_product in db_products:
            resutl.append(db_product.trello_card_id)
    return resutl
