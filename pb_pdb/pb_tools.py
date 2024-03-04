import pb_admin
from pb_admin import schemas as pb_schemas
import os
from pb_pdb import schemas, db_tools, space_tools
import mimetypes
from loguru import logger
from time import sleep
import requests
from urllib.parse import urlparse


SITE_URL = os.environ.get('SITE_URL', '')
LOGIN_PB = os.environ.get('LOGIN_PB', '')
PASS_PB = os.environ.get('PASS_PB', '')


def get_valid_tags_ids(tag_names: list[str]) -> list[int]:
    tag_names = [tag_name.lower() for tag_name in tag_names]
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    result = []
    for tag_name in tag_names:
        pb_tags = pb_session.tags.get_list(search=tag_name)
        for pb_tag in pb_tags:
            if pb_tag.name.lower() == tag_name.lower():
                tag_for_add = pb_session.tags.get(pb_tag.ident)
                break
        else:
            tag_for_add = pb_session.tags.fill_scheme_by_policy(
                 pb_schemas.Tag(
                     name=tag_name,
                 )
            )
            tag_for_add = pb_session.tags.create(tag_for_add)
        result.append(tag_for_add.ident)
    return result


def bulk_add_tag(task: schemas.BulkTag):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    pb_tags = pb_session.tags.get_list(search=task.tag)
    for pb_tag in pb_tags:
        if pb_tag.name.lower() == task.tag.lower():
            tag_for_add = pb_session.tags.get(pb_tag.ident)
            tag_for_add = pb_session.tags.fill_scheme_by_policy(tag_for_add)
            pb_session.tags.update(tag_for_add, is_lite=True)
            break
    else:
        tag_for_add = pb_session.tags.fill_scheme_by_policy(
             pb_schemas.Tag(
                 name=task.tag,
             )
        )
        tag_for_add = pb_session.tags.create(tag_for_add)
    for product in task.products:
        sleep(0.5)
        _product = pb_session.products.get(product.ident, product.product_type)
        if tag_for_add.ident in _product.tags_ids:
            continue
        _product.tags_ids.append(tag_for_add.ident)
        pb_session.products.update(_product, is_lite=True)
    db_tools.rm_bulk_tag_task(task.db_id)


def add_tags(product_id: int, product_type: pb_schemas.ProductType, tags: list[str]):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    _product = pb_session.products.get(product_id, product_type)
    pb_tags = pb_session.tags.get_list()
    for tag in tags:
        for pb_tag in pb_tags:
            if pb_tag.name.lower() == tag.lower():
                tag_for_add = pb_session.tags.get(pb_tag.ident)
                break
        else:
            tag_for_add = pb_session.tags.fill_scheme_by_policy(
                 pb_schemas.Tag(
                     name=tag,
                 )
            )
            tag_for_add = pb_session.tags.create(tag_for_add)

        if tag_for_add.ident in _product.tags_ids:
            continue
        _product.tags_ids.append(tag_for_add.ident)
    pb_session.products.update(_product, is_lite=True)


def get_category_ids_by_names(category_names: list[str]) -> list[int]:
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    result = []
    for category_name in category_names:
        pb_categories = pb_session.categories.get_list(category_name)
        for pb_category in pb_categories:
            if pb_category.title.lower() == category_name.lower():
                result.append(pb_category.ident)
    return result


def get_format_ids_by_names(format_names: list[str]) -> list[int]:
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    result = []
    for format_name in format_names:
        pb_formats = pb_session.formats.get_list(format_name)
        for pb_format in pb_formats:
            if pb_format.title.lower() == format_name.lower():
                result.append(pb_format.ident)
    return result


def get_compatibilities_ids_by_names(compatibility_names: list[str]) -> list[int]:
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    result = []
    for compatibility_name in compatibility_names:
        pb_compatibilities = pb_session.compatibilities.get_list(compatibility_name)
        for pb_compatibility in pb_compatibilities:
            if pb_compatibility.title.lower() == compatibility_name.lower():
                result.append(pb_compatibility.ident)
    return result


def _make_img_scheme_from_s3_url(url: str, alt: str) -> pb_schemas.Image:
    if not url:
        return None
    file_name = space_tools.get_filename_from_url(url)
    data = requests.get(url).content
    return pb_schemas.Image(
        file_name=file_name,
        mime_type=mimetypes.guess_type(url)[0],
        data=data,
        alt=alt,
    )


def upload_product(
    product: schemas.UploadFreebie | schemas.UploadPlus | schemas.UploadPrem,
    product_files: schemas.ProductFiles,
) -> pb_schemas.Product:
    if isinstance(product, schemas.UploadFreebie):
        product_type = pb_schemas.ProductType.freebie
    elif isinstance(product, schemas.UploadPlus):
        product_type = pb_schemas.ProductType.plus
    elif isinstance(product, schemas.UploadPrem):
        product_type = pb_schemas.ProductType.premium
    else:
        raise ValueError('Wrong product type')

    category_ids = get_category_ids_by_names(product.categories)
    tags_ids = get_valid_tags_ids(product.tags)
    new_product = pb_schemas.Product(
        product_type=product_type,
        created_at=product.date_upload,
        title=product.title,
        slug=product.slug,
        is_live=False if product.schedule_date else True,
        size=product.size,
        short_description=product.excerpt,
        description=product.description,
        thumbnail=_make_img_scheme_from_s3_url(product_files.thumbnail_url, product.meta_title),
        thumbnail_retina=_make_img_scheme_from_s3_url(product_files.thumbnail_x2_url, product.meta_title),
        push_image=_make_img_scheme_from_s3_url(product_files.push_url, product.meta_title),
        main_image=_make_img_scheme_from_s3_url(product_files.main_img_url, product.meta_title),
        main_image_retina=_make_img_scheme_from_s3_url(product_files.main_img_x2_url, product.meta_title),
        gallery_images=list(map(_make_img_scheme_from_s3_url, product_files.gallery_x2_urls, product.meta_title)),
        gallery_images_retina=list(map(_make_img_scheme_from_s3_url, product_files.gallery_x2_urls, product.meta_title)),
        vps_path=urlparse(product_files.product_url).path.strip('/'),
        s3_path=urlparse(product_files.product_s3_url).path.strip('/'),
        meta_title=product.meta_title,
        meta_description=product.meta_description,
        category_ids=category_ids,
        tags_ids=tags_ids,
    )
    if product_type == pb_schemas.ProductType.freebie:
        new_product.email_download = product.download_by_email
        new_product.count_downloads = 3
        new_product.format_ids = get_format_ids_by_names(product.formats)
        new_product.author_name = product.guest_author
        new_product.author_url = product.guest_author_link
    elif product_type == pb_schemas.ProductType.plus:
        new_product.format_ids = get_format_ids_by_names(product.formats)
        new_product.count_downloads = 3
        new_product.author_name = product.guest_author
        new_product.author_url = product.guest_author_link
    elif product_type == pb_schemas.ProductType.premium:
        new_product.standard_price = product.sale_standart_price if product.sale_standart_price else product.standart_price
        new_product.extended_price = product.sale_extended_price if product.sale_extended_price else product.extended_price
        new_product.standard_price_old = product.standart_price if product.sale_standart_price else None
        new_product.extended_price_old = product.extended_price if product.sale_extended_price else None
        new_product.inner_short_description = product.excerpt
        new_product.premium_thumbnail = _make_img_scheme_from_s3_url(product_files.thumbnail_url, product.meta_title)
        new_product.premium_thumbnail_retina = _make_img_scheme_from_s3_url(product_files.thumbnail_x2_url, product.meta_title)
        new_product.features_short = [
            pb_admin.schemas.FeatureShort(
                title='Format',
                value=', '.join(product.formats),
            ),
            pb_admin.schemas.FeatureShort(
                title='File size',
                value=product.size,
            )
        ]
        new_product.compatibilities_ids = get_compatibilities_ids_by_names(product.compatibilities)
        new_product.gallery_images = [new_product.main_image] + new_product.gallery_images
        new_product.gallery_images_retina = [new_product.main_image_retina] + new_product.gallery_images_retina
    logger.debug(f'''Product scheme:
                 ident = {new_product.ident}
                product_type = {new_product.product_type}
                url = {new_product.url}
                title = {new_product.title}
                created_at = {new_product.created_at}
                slug = {new_product.slug}
                is_live = {new_product.is_live}
                size = {new_product.size}
                show_statistic = {new_product.show_statistic}
                email_download = {new_product.email_download}
                count_downloads = {new_product.count_downloads}
                short_description = {new_product.short_description}
                description = {new_product.description}
                thumbnail = {'Field' if new_product.thumbnail else 'None'}
                thumbnail_retina = {'Field' if new_product.thumbnail_retina else 'None'}
                premium_thumbnail = {'Field' if new_product.premium_thumbnail else 'None'}
                premium_thumbnail_retina = {'Field' if new_product.premium_thumbnail_retina else 'None'}
                push_image = {'Field' if new_product.push_image else 'None'}
                vps_path = {new_product.vps_path}
                s3_path = {new_product.s3_path}
                main_image = {'Field' if new_product.main_image else 'None'}
                gallery_images = {'Field' if new_product.gallery_images else 'None'}
                main_image_retina = {'Field' if new_product.main_image_retina else 'None'}
                gallery_images_retina = {'Field' if new_product.gallery_images_retina else 'None'}
                author_name = {new_product.author_name}
                author_url = {new_product.author_url}
                features = {new_product.features}
                category_ids = {new_product.category_ids}
                format_ids = {new_product.format_ids}
                font_ids = {new_product.font_ids}
                meta_title = {new_product.meta_title}
                meta_description = {new_product.meta_description}
                meta_keywords = {new_product.meta_keywords}
                tags_ids = {new_product.tags_ids}
                extended_price = {new_product.extended_price}
                standard_price = {new_product.standard_price}
                extended_price_old = {new_product.extended_price_old}
                standard_price_old = {new_product.standard_price_old}
                compatibilities_ids = {new_product.compatibilities_ids}
                inner_short_description = {new_product.inner_short_description}
                free_sample_link_url = {new_product.free_sample_link_url}
                free_sample_link_text = {new_product.free_sample_link_text}
                free_sample_description = {new_product.free_sample_description}
                live_preview_type = {new_product.live_preview_type}
                card_title = {new_product.card_title}
                card_button_link = {new_product.card_button_link}
                card_button_text = {new_product.card_button_text}
                card_description = {new_product.card_description}
                live_preview_link = {new_product.live_preview_link}
                live_preview_text = {new_product.live_preview_text}
                button_text = {new_product.button_text}
                custom_url_title = {new_product.custom_url_title}
                custom_url = {new_product.custom_url}
                old_img = {'Field' if new_product.old_img else 'None'}
                old_img_retina = {'Field' if new_product.old_img_retina else 'None'}
                download_link_text = {new_product.download_link_text}
                download_link_url = {new_product.download_link_url}
                author_id = {new_product.author_id}
                features_short = {new_product.features_short}
    ''')
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    return pb_session.products.create(new_product)


def make_push(
    product_id: int,
    product: schemas.UploadFreebie | schemas.UploadPlus | schemas.UploadPrem
):
    if isinstance(product, schemas.UploadFreebie):
        product_type = pb_schemas.ProductType.freebie
    elif isinstance(product, schemas.UploadPlus):
        product_type = pb_schemas.ProductType.plus
    elif isinstance(product, schemas.UploadPrem):
        product_type = pb_schemas.ProductType.premium
    else:
        raise ValueError('Wrong product type')
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    pb_session.tools.make_push(product_id, product_type)


def make_life(product_id: int, product_type: pb_schemas.ProductType):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    product = pb_session.products.get(product_id, product_type)
    product.is_live = True
    pb_session.products.update(product, is_lite=True)
