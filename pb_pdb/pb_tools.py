import pb_admin
import os
from pb_pdb import schemas, db_tools
from loguru import logger

SITE_URL = os.environ.get('SITE_URL', '')
LOGIN_PB = os.environ.get('LOGIN_PB', '')
PASS_PB = os.environ.get('PASS_PB', '')


def check_tags(tag_names: list[str], category_names: list[str]):
    tag_names = [tag_name.lower() for tag_name in tag_names]
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    pb_tags: list[pb_admin.schemas.Tag] = pb_session.tags.get_list()
    pb_categories: list[pb_admin.schemas.Cattegory] = pb_session.categories.get_list()

    existed_tag_names = [tag.name for tag in pb_tags if tag.name in tag_names]
    existed_tags = [pb_session.tags.get(tag.ident) for tag in pb_tags if tag.name in tag_names]
    new_tags = [tag_name for tag_name in tag_names if tag_name not in existed_tag_names]
    for new_tag in new_tags:
        pb_session.tags.create(pb_admin.schemas.Tag(
            name=new_tag,
            title=new_tag.capitalize(),
            category_ids=[category.ident for category in pb_categories if category.title in category_names]
        ))
    for existed_tag in existed_tags:
        tag_category_ids = set(existed_tag.category_ids)
        product_category_ids = set([category.ident for category in pb_categories if category.title in category_names])
        if not tag_category_ids.intersection(product_category_ids):
            existed_tag.category_ids.extend(list(product_category_ids))
            pb_session.tags.update(existed_tag)


def bulk_add_tag(task: schemas.BulkTag):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    pb_categories = pb_session.categories.get_list()
    if task.category_id not in [category.ident for category in pb_categories]:
        db_tools.rm_bulk_tag_task(task.db_id)
        logger.error(f'Category with id {task.category_id} not found')
    pb_tags = pb_session.tags.get_list()
    for pb_tag in pb_tags:
        if pb_tag.name.lower() == task.tag.lower():
            tag_for_add = pb_session.tags.get(pb_tag.ident)
            if task.category_id in tag_for_add.category_ids:
                break
            else:
                tag_for_add.category_ids.append(task.category_id)
                pb_session.tags.update(tag_for_add, is_lite=True)
                break
    else:
        tag_for_add = pb_session.tags.create(pb_admin.schemas.Tag(
            name=task.tag,
            title=task.tag.capitalize(),
            category_ids=[task.category_id]
        ))
    for product in task.products:
        _product = pb_session.products.get(product.ident, product.product_type)
        if task.category_id not in _product.category_ids:
            continue
        if task.tag in _product.tags_ids:
            continue
        _product.tags_ids.append(tag_for_add.ident)
        pb_session.products.update(_product, is_lite=True)
    db_tools.rm_bulk_tag_task(task.db_id)
