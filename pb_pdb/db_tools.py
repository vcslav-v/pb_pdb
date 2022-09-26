from typing import Optional

from pb_pdb import dropbox_tools, models, schemas
from pb_pdb.db import SessionLocal


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
            session.add(db_product)
        if db_product.category != category:
            category.number_products_created += 1
            db_product.readable_uid = f'{category.prefix}{category.number_products_created}'
        db_product.work_title = product.title
        db_product.description = product.description
        db_product.designer = db_designer
        db_product.category = category

        if product.parrent_id:
            db_parrent = session.query(models.Product).filter_by(
                trello_card_id=product.parrent_id
            ).first()
            db_product.parent = db_parrent
            db_product.readable_uid = f'{db_product.readable_uid} ({db_parrent.readable_uid})'

        full_product_name = f'{db_product.readable_uid} - {product.title}'
        db_product.work_directory = dropbox_tools.make_directory(full_product_name)
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


def make_final_text(card_id: str, title: str, description: str):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        dropbox_tools.rename(db_product.work_directory, title)
        db_product.title = title
        db_product.description = description
        session.commit()
