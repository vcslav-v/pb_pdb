from datetime import datetime
from math import ceil
import re
from typing import Optional

from sqlalchemy import and_, func
import pandas as pd

from pb_pdb import dropbox_tools, models, schemas, trello_tools, config
from pb_pdb.db import SessionLocal
from PIL import Image
import io

from loguru import logger

PRODUCTS_ON_PAGE = 12
RESIZE_COVER_WIDTH = 640
IMG_PRODUCT_IMG_TEMPLATE = 'https://pb-pdb.herokuapp.com/api/trello_product/img/{trello_card_id}'


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


def make_final_text(
    card_id: str,
    card_name: str,
    title: str,
    description: str,
    is_big_product: bool = False,
    is_extra_product: bool = False,
):
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
        db_product.is_big_product = is_big_product
        db_product.is_extra = is_extra_product
        session.commit()


def publish_product(card_id: str):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        if not db_product.end_production_date:
            end_production_date = trello_tools.get_end_production_date(card_id)
            if end_production_date:
                db_product.end_production_date = end_production_date
            else:
                db_product.end_production_date = datetime.utcnow().date()
        db_product.end_date = datetime.utcnow().date()
        db_product.done = True
        session.commit()


def get_products(filter_data: schemas.FilterPage) -> schemas.ProductPage:
    result = schemas.ProductPage()
    result.page = filter_data.page
    page_start = PRODUCTS_ON_PAGE * (filter_data.page - 1)
    page_end = PRODUCTS_ON_PAGE * filter_data.page
    with SessionLocal() as session:
        query = session.query(models.Product)

        if filter_data.designer_id:
            query = query.filter_by(designer_id=filter_data.designer_id)
        if filter_data.category_id:
            query = query.filter_by(category_id=filter_data.category_id)
        if filter_data.end_design_date_start and filter_data.end_design_date_end:
            query = query.filter(
                and_(
                    models.Product.end_production_date >= filter_data.end_design_date_start,
                    models.Product.end_production_date <= filter_data.end_design_date_end,
                )
            )
        query = query.filter(models.Product.is_extra == filter_data.is_extra)
        query.order_by(models.Product.end_production_date.desc())

        all_db_products = query.count()
        result.number_products = all_db_products
        result.number_pages = ceil(all_db_products / PRODUCTS_ON_PAGE)
        db_products = query.slice(page_start, page_end)

        query = session.query(models.Product).filter_by(is_big_product=True)
        if filter_data.designer_id:
            query = query.filter_by(designer_id=filter_data.designer_id)
        if filter_data.category_id:
            query = query.filter_by(category_id=filter_data.category_id)
        if filter_data.end_design_date_start and filter_data.end_design_date_end:
            query = query.filter(
                and_(
                    models.Product.end_production_date >= filter_data.end_design_date_start,
                    models.Product.end_production_date <= filter_data.end_design_date_end,
                )
            )
        query = query.filter(models.Product.is_extra == filter_data.is_extra)

        result.number_big_products = query.count()

        query = session.query(func.sum(models.Product.adobe_count))
        if filter_data.designer_id:
            query = query.filter_by(designer_id=filter_data.designer_id)
        if filter_data.category_id:
            query = query.filter_by(category_id=filter_data.category_id)
        if filter_data.end_design_date_start and filter_data.end_design_date_end:
            query = query.filter(
                and_(
                    models.Product.end_production_date >= filter_data.end_design_date_start,
                    models.Product.end_production_date <= filter_data.end_design_date_end,
                )
            )
        query = query.filter(models.Product.is_extra == filter_data.is_extra)
        result.total_adobe_count = query.scalar() or 0

        for db_product in db_products:
            result.products.append(schemas.ProductInPage(
                ident=db_product.id,
                title=db_product.title if db_product.title else db_product.work_title,
                designer_name=db_product.designer.full_name,
                category=db_product.category.name,
                trello_link=db_product.trello_link,
                start_date=db_product.start_date,
                is_big=db_product.is_big_product,
                is_extra=db_product.is_extra,
                adobe_count=db_product.adobe_count or 0,
            ))
            if db_product.end_production_date:
                result.products[-1].end_production_date = db_product.end_production_date
    return result


def get_products_done() -> list[str]:
    with SessionLocal() as session:
        db_products = session.query(models.Product).filter_by(done=True).all()
        resutl = []
        for db_product in db_products:
            resutl.append(db_product.trello_card_id)
    return resutl


def get_common_data() -> schemas.ProductPageData:
    with SessionLocal() as session:
        page = schemas.ProductPageData()
        db_employees = session.query(models.Employee).filter(models.Employee.products_as_designer).all()
        for db_employee in db_employees:
            page.designers.append(
                schemas.Designer(
                    ident=db_employee.id,
                    name=db_employee.full_name,
                )
            )
        db_categories = session.query(models.Category).filter(models.Category.products).all()
        for db_category in db_categories:
            page.categories.append(
                schemas.Category(
                    ident=db_category.id,
                    name=db_category.name,
                )
            )
    return page


def production_end(card_id: str):
    with SessionLocal() as session:
        db_product = session.query(models.Product).filter_by(
            trello_card_id=card_id
        ).first()
        db_product.end_production_date = datetime.utcnow().date()
        session.commit()


def set_status(prefix: str, status: str):
    with SessionLocal() as session:
        db_upload_status = session.query(models.UploadStatus).filter_by(
            prefix=prefix
        ).first()
        if not db_upload_status:
            db_upload_status = models.UploadStatus(
                prefix=prefix,
            )
            session.add(db_upload_status)
        db_upload_status.status = status
        session.commit()


def get_status(prefix: str):
    with SessionLocal() as session:
        db_upload_status = session.query(models.UploadStatus).filter_by(
            prefix=prefix
        ).first()
        if not db_upload_status:
            return
        return db_upload_status.status


def add_to_product_schedule(schedule_date: datetime, edit_url: str, title: str):
    with SessionLocal() as session:
        new_row = models.ProductSchedule(
            date_time=schedule_date,
            edit_url=edit_url,
            name=title,
        )
        session.add(new_row)
        session.commit()


def rm_product_schedule(id: int):
    with SessionLocal() as session:
        product_row = session.query(models.ProductSchedule).filter_by(
            id=id
        ).first()
        session.delete(product_row)
        session.commit()


def update_product_schedule(id: int, date_time: datetime):
    with SessionLocal() as session:
        product_row = session.query(models.ProductSchedule).filter_by(
            id=id
        ).first()
        product_row.date_time = date_time
        session.commit()


def get_product_schedule(publish_date_time: datetime = None):
    with SessionLocal() as session:
        if publish_date_time:
            schedule = session.query(models.ProductSchedule).filter(
                models.ProductSchedule.date_time <= publish_date_time
            ).all()
        else:
            schedule = session.query(models.ProductSchedule).order_by(
                models.ProductSchedule.date_time
            ).all()
        return schedule


def set_uploader_callback(callback_data: schemas.UploaderResponse, prefix: str):
    with SessionLocal() as session:
        callback = models.Callback(
            prefix=prefix,
            data=callback_data.json()
        )
        session.add(callback)
        session.commit()


def get_callback_data(prefix: str):
    with SessionLocal() as session:
        callback = session.query(models.Callback).filter_by(
            prefix=prefix
        ).first()
        if callback:
            return callback.data


def rm_callback(prefix: str):
    with SessionLocal() as session:
        callback = session.query(models.Callback).filter_by(
            prefix=prefix
        ).first()
        session.delete(callback)
        session.commit()


def resize_image_with_max_width(image, max_width):
    width, height = image.size
    if width > max_width:
        ratio = max_width / width
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return image.resize((new_width, new_height))
    return image


def set_covers():
    with SessionLocal() as session:
        query = session.query(models.Product)
        query = query.filter(models.Product.end_production_date != None)
        query = query.filter(models.Product.cover == None)
        products: list[models.Product] = query.all()
        for product in products:
            try:
                img_file = io.BytesIO(dropbox_tools.get_cover_file_content(product.work_directory))
            except:
                continue
            img = Image.open(img_file)
            img = resize_image_with_max_width(img, RESIZE_COVER_WIDTH)
            img = img.convert('RGB')
            output_image_file = io.BytesIO()
            img.save(output_image_file, format='JPEG')
            output_image_file.seek(0)
            product.cover = output_image_file.getvalue()
            logger.debug(f'Product {product.id} has cover')

        session.commit()


def get_product_img(product_id: int):
    with SessionLocal() as session:
        product = session.query(models.Product).filter_by(
            id=product_id
        ).first()
        return product.cover


def refresh_adobe():
    batch_size = 100
    with SessionLocal() as session:
        last_id = 0
        while True:
            products = (
                session.query(models.Product)
                .filter(models.Product.id > last_id)
                .order_by(models.Product.id)
                .limit(batch_size)
                .all()
            )
            if not products:
                break
            for product in products:
                product.adobe_count = dropbox_tools.get_adobe_count(product.work_directory)
                if not product.is_big_product and product.adobe_count == 0:
                    product.adobe_count = 1
                logger.debug(f'Product {product.readable_uid} has {product.adobe_count} adobe files')
                last_id = product.id
            session.commit()


def set_bulk_tag_task(task: schemas.BulkTag):
    with SessionLocal() as session:
        session.add(models.BulkTagTask(
            value=task.model_dump_json(),
        ))
        session.commit()


def get_bulk_tag_task():
    with SessionLocal() as session:
        active_task = session.query(models.BulkTagTask).filter_by(
            in_progress=True
        ).first()
        if active_task:
            return
        task = session.query(models.BulkTagTask).filter_by(
            in_progress=False
        ).first()
        if task:
            task.in_progress = True
            session.commit()
            result = schemas.BulkTag.model_validate_json(task.value)
            result.db_id = task.id
            return result


def rm_bulk_tag_task(db_id: int):
    with SessionLocal() as session:
        task = session.query(models.BulkTagTask).filter_by(
            id=db_id
        ).first()
        session.delete(task)
        session.commit()


def get_bulk_tag_count_tasks() -> int:
    with SessionLocal() as session:
        return session.query(models.BulkTagTask).count()


def deactivate_bulk_tag_task(db_id: int):
    with SessionLocal() as session:
        task = session.query(models.BulkTagTask).filter_by(
            id=db_id
        ).first()
        task.in_progress = False
        session.commit()


def _extract_tags(text: str) -> list[str] | None:
    """
    Извлекает список тегов из строки.
    Теги читаются ТОЛЬКО до конца строки (до перевода строки).
    Возвращает None, если теги не найдены.
    """

    if not text or not isinstance(text, str):
        return None

    pattern = re.compile(
        r"""
        (?:\*\*\s*)?        # необязательные **
        теги                # слово "теги"
        (?:\s*\*\*)?        # необязательные **
        \s*:\s*             # двоеточие
        ([^\r\n]+)          # ВСЁ до конца строки
        """,
        re.IGNORECASE | re.VERBOSE
    )

    match = pattern.search(text)
    if not match:
        return None

    raw_tags = match.group(1)

    tags = [
        tag.lower().strip()
        for tag in raw_tags.split(',')
        if tag.strip()
    ]

    return tags or None


def get_all_products_data():
    with SessionLocal() as session:
        products = (
            session.query(
                models.Product.trello_card_id,
                models.Product.readable_uid,
                models.Product.description,
                models.Product.work_title,
                models.Product.title,
                models.Category.name.label("category"),
                models.Product.dropbox_share_url,
                models.Product.trello_link,
                models.Product.done,
                models.Product.cover.isnot(None).label("has_cover"),
            )
            .join(models.Category, models.Product.category_id == models.Category.id)
        )

        rows = products.all()

        df = pd.DataFrame(rows, columns=[
            "trello_card_id",
            "readable_uid",
            "work_title",
            "title",
            "category",
            "dropbox_share_url",
            "trello_link",
            "done",
            "has_cover",
        ])

        df["img_url"] = df.apply(
            lambda row: (
                config.IMG_PRODUCT_IMG_TEMPLATE.format(
                    trello_card_id=row["trello_card_id"]
                )
                if row["has_cover"]
                else None
            ),
            axis=1,
        )

        df = df.drop(columns=["trello_card_id", "has_cover", "description"])

        table_name = "pb_trello_products"
        yield table_name, df
    
    tag_connections = []
    for row in rows:
        if not row.description:
            continue
        tags = _extract_tags(row.description)
        if not tags:
            continue
        _tag_connections = [{
            "readable_uid": row.readable_uid,
            "tag": t.strip(),
        } for t in tags]
        tag_connections.extend(_tag_connections)
    df_tags = pd.DataFrame(tag_connections, columns=[
        "readable_uid",
        "tag",
    ])
    table_name = "pb_trello_product_tags"
    yield table_name, df_tags

def get_trello_cover(trello_card_id: str):
    with SessionLocal() as session:
        product = session.query(models.Product).filter_by(
            trello_card_id=trello_card_id
        )
        product = product.first()
        if not product:
            return
        return product.cover