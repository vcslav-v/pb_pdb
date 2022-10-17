from typing import Optional
from urllib.parse import urlparse

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


def publish_product(card_id: str, links: dict):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        if db_product.market_place_links:
            db_links = db_product.market_place_links
        else:
            db_links = models.MarketPlaceLink()
            session.add(db_links)
        if links.get('PB link') and urlparse(links.get('PB link')).netloc:
            db_links.pixelbuddha = links.get('PB link')
        elif links.get('CM link') and urlparse(links.get('CM link')).netloc:
            db_links.creative_market = links.get('CM link')
        elif links.get('YWFT link') and urlparse(links.get('YWFT link')).netloc:
            db_links.you_work_for_them = links.get('YWFT link')
        elif links.get('Yellow Images link') and urlparse(links.get('Yellow Images link')).netloc:
            db_links.yellow_images = links.get('Yellow Images link')
        elif links.get('DC link') and urlparse(links.get('DC link')).netloc:
            db_links.designcuts = links.get('DC link')
        elif links.get('Elements link') and urlparse(links.get('Elements link')).netloc:
            db_links.elements = links.get('Elements link')
        elif links.get('Artstation link') and urlparse(links.get('Artstation link')).netloc:
            db_links.art_station = links.get('Artstation link')
        elif links.get('Freepik link') and urlparse(links.get('Freepik link')).netloc:
            db_links.freepick = links.get('Freepik link')
        elif links.get('Adobe Stock link') and urlparse(links.get('Adobe Stock link')).netloc:
            db_links.adobe_stock = links.get('Adobe Stock link')
        elif links.get('Graphicriver link') and urlparse(links.get('Graphicriver link')).netloc:
            db_links.graphicriver = links.get('Graphicriver link')
        elif links.get('Etsy link') and urlparse(links.get('Etsy link')).netloc:
            db_links.etsy = links.get('Etsy link')
        
        db_product.market_place_links = db_links
        db_product.done = True
        session.commit()
