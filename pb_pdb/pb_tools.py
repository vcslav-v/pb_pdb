import pb_admin
import os

SITE_URL = os.environ.get('SITE_URL', '')
LOGIN_PB = os.environ.get('LOGIN_PB', '')
PASS_PB = os.environ.get('PASS_PB', '')


def check_tags(tag_names: list[str], category_names: list[str]):
    tag_names = [tag_name.lower() for tag_name in tag_names]
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    pb_tags: list[pb_admin.schemas.Tag] = pb_session.tags.get_list()
    pb_categories: list[pb_admin.schemas.Cattegory] = pb_session.categories.get_list()

    existed_tags = [tag.name for tag in pb_tags if tag.name in tag_names]
    existed_tags = [pb_session.tags.get(tg.ident) for tg in existed_tags]

    new_tags = [tag_name for tag_name in tag_names if tag_name not in existed_tags]
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
