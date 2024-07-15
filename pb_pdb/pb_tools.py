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


def get_creator_id_by_name(creator_name: str | None, creator_link: str | None) -> int:
    if not creator_name or not creator_link:
        return 1
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    creators = pb_session.creators.get_list()
    for creator in creators:
        if creator.name.lower() == creator_name.lower().strip():
            return creator.ident
    new_creator = pb_schemas.Creator(
        name=creator_name,
        link=creator_link,
        description=creator_name,
    )
    creator = pb_session.creators.create(new_creator)
    return creator.ident


def get_category_id_by_names(category_names: list[str]) -> int | None:
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB)
    for category_name in category_names:
        pb_categories = pb_session.categories.get_list(category_name)
        for pb_category in pb_categories:
            if pb_category.title.lower() == category_name.lower():
                return pb_category.ident


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


def _make_raw_presentation(images: list[pb_admin.schemas.Image]) -> list[list[pb_admin.schemas.ProductLayoutImg | pb_admin.schemas.ProductLayoutVideo]]:
    result = []
    for i in range(len(images)):
        result.append([pb_admin.schemas.ProductLayoutImg(img_n=i)])
    return result


def upload_product(
    product: schemas.UploadFreebie | schemas.UploadPlus | schemas.UploadPrem,
    product_files: schemas.ProductFiles,
) -> pb_schemas.Product:
    if isinstance(product, schemas.UploadFreebie):
        product_type = pb_schemas.NewProductType.freebie
        price_commercial_cent = 0
        price_extended_cent = None if product.guest_author else 4900
        price_commercial_sale_cent = None
        price_extended_sale_cent = None
    elif isinstance(product, schemas.UploadPlus):
        product_type = pb_schemas.NewProductType.plus
        price_commercial_cent = 0 if product.guest_author else 1700
        price_extended_cent = None if product.guest_author else 9900
        price_commercial_sale_cent = None
        price_extended_sale_cent = None
    elif isinstance(product, schemas.UploadPrem):
        product_type = pb_schemas.NewProductType.premium
        price_commercial_cent = product.standart_price * 100
        price_extended_cent = product.extended_price * 100
        price_commercial_sale_cent = product.sale_standart_price * 100 if product.sale_standart_price else None
        price_extended_sale_cent = product.sale_extended_price * 100 if product.sale_extended_price else None
    else:
        raise ValueError('Wrong product type')

    category_id = get_category_id_by_names(product.categories)
    if not category_id:
        raise ValueError('Category not found')
    creator_id = get_creator_id_by_name(product.guest_author, product.guest_author_link)
    tags_ids = get_valid_tags_ids(product.tags)
    images = [
        _make_img_scheme_from_s3_url(product_files.main_img_x2_url, product.meta_title),
    ] + [
        _make_img_scheme_from_s3_url(url, product.meta_title) for url in product_files.gallery_x2_urls
    ]
    new_product = pb_schemas.NewProduct(
        title=product.title,
        slug=product.slug,
        created_at=product.date_upload,
        is_live=False if product.schedule_date else True,
        product_type=product_type,
        only_registered_download=product.download_by_email if isinstance(product, schemas.UploadFreebie) else False,
        creator_id=creator_id,
        size=product.size,
        category_id=category_id,
        excerpt=product.excerpt,
        description=product.description,
        price_commercial_cent=price_commercial_cent,
        price_extended_cent=price_extended_cent,
        price_commercial_sale_cent=price_commercial_sale_cent,
        price_extended_sale_cent=price_extended_sale_cent,
        thumbnail=_make_img_scheme_from_s3_url(product_files.thumbnail_x2_url, product.meta_title),
        push_image=_make_img_scheme_from_s3_url(product_files.push_url, product.meta_title),
        images=images,
        presentation=_make_raw_presentation(images),
        vps_path=urlparse(product_files.product_url).path.strip('/'),
        s3_path=urlparse(product_files.product_s3_url).path.strip('/'),
        tags_ids=tags_ids,
        formats=', '.join(product.formats),
        meta_title=product.meta_title,
        meta_description=product.meta_description,
        meta_keywords=None,
    )
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    return pb_session.new_products.create(new_product)


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


def make_life(product_id: int):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    product = pb_session.new_products.get(product_id)
    product.is_live = True
    pb_session.products.update(product, is_lite=True)


def new_product(product: pb_schemas.Product):
    pb_session = pb_admin.PbSession(SITE_URL, LOGIN_PB, PASS_PB, edit_mode=True)
    pb_session.new_products.create(_old_product_to_new(product, pb_session))


# Delete after new_product
def _get_format_str(pb_session: pb_admin.PbSession):
    formats = pb_session.formats.get_list()

    def inner(format_ids: list[int]):
        result = []
        for f in formats:
            if f.ident in format_ids:
                result.append(f.title)
        return ', '.join(result)

    return inner


def _get_creator_id(product: pb_admin.schemas.Product, pb_session: pb_admin.PbSession) -> int | None:
    if not product.author_name:
        return None
    creators = pb_session.creators.get_list()
    for c in creators:
        if c.name.lower() == product.author_name.lower():
            return c.ident
    new_creator = pb_admin.schemas.Creator(
        name=product.author_name,
        link=product.author_url,
        description=product.author_name,
    )
    creator = pb_session.creators.create(new_creator)
    return creator.ident


def _make_raw_img(old_img: pb_admin.schemas.Image, pb_session: pb_admin.PbSession) -> pb_admin.schemas.Image:
    url = old_img.original_url.replace('//storage', '/storage')
    img_data = pb_session.session.get(url)
    img_data.raise_for_status()
    img_data = img_data.content
    return pb_admin.schemas.Image(
        data=img_data,
        mime_type=old_img.mime_type,
        file_name=old_img.file_name,
        alt=old_img.alt,
    )


def _make_raw_presentation(images: list[pb_admin.schemas.Image]) -> list[list[pb_admin.schemas.ProductLayoutImg | pb_admin.schemas.ProductLayoutVideo]]:
    result = []
    for i in range(len(images)):
        result.append([pb_admin.schemas.ProductLayoutImg(img_n=i)])
    return result


def _old_product_to_new(old_product: pb_admin.schemas.Product, pb_session: pb_admin.PbSession) -> pb_admin.schemas.NewProduct:
    get_format_str = _get_format_str(pb_session)
    product_types = {
        pb_admin.schemas.ProductType.freebie: pb_admin.schemas.NewProductType.freebie,
        pb_admin.schemas.ProductType.plus: pb_admin.schemas.NewProductType.plus,
        pb_admin.schemas.ProductType.premium: pb_admin.schemas.NewProductType.premium,
    }

    # Prices
    FREEBIE_PRICE_EXT = 4900
    PLUS_PRICE = 1700
    PLUS_PRICE_EXT = 9900
    if old_product.product_type == pb_admin.schemas.ProductType.freebie:
        price_commercial_cent = 0
        if old_product.author_name:
            price_extended_cent = None
        else:
            price_extended_cent = FREEBIE_PRICE_EXT
        price_commercial_sale_cent = None
        price_extended_sale_cent = None
    elif old_product.product_type == pb_admin.schemas.ProductType.plus:
        if old_product.author_name:
            price_commercial_cent = 0
            price_extended_cent = None
        else:
            price_commercial_cent = PLUS_PRICE
            price_extended_cent = PLUS_PRICE_EXT
        price_commercial_sale_cent = None
        price_extended_sale_cent = None
    elif old_product.product_type == pb_admin.schemas.ProductType.premium:
        price_commercial_cent = old_product.standard_price_old if old_product.standard_price_old else old_product.standard_price
        price_commercial_cent = price_commercial_cent * 100
        price_extended_cent = old_product.extended_price if old_product.extended_price else old_product.extended_price_old
        price_extended_cent = price_extended_cent * 100
        price_commercial_sale_cent = old_product.standard_price if old_product.standard_price_old else None
        price_commercial_sale_cent = price_commercial_sale_cent * 100 if price_commercial_sale_cent else None
        price_extended_sale_cent = old_product.extended_price if old_product.extended_price_old else None
        price_extended_sale_cent = price_extended_sale_cent * 100 if price_extended_sale_cent else None

    # Images
    images = []
    if old_product.main_image_retina:
        images.append(old_product.main_image_retina)
    elif old_product.main_image:
        images.append(old_product.main_image)
    elif old_product.old_img_retina:
        images.append(old_product.old_img_retina)
    elif old_product.old_img:
        images.append(old_product.old_img)

    if old_product.product_type != pb_admin.schemas.ProductType.premium:
        if old_product.gallery_images_retina:
            images.extend(old_product.gallery_images_retina)
        elif old_product.gallery_images:
            images.extend(old_product.gallery_images)
    else:
        if old_product.gallery_images_retina:
            images.extend(old_product.gallery_images_retina[1:])
        elif old_product.gallery_images:
            images.extend(old_product.gallery_images[1:])

    # Buttons
    if old_product.product_type != pb_admin.schemas.ProductType.premium and (old_product.custom_url or old_product.card_button_link or old_product.live_preview_link):
        custom_btn_text = old_product.custom_url_title or old_product.live_preview_text or old_product.button_text or old_product.card_button_text or 'Download'
        custom_btn_url = old_product.custom_url or old_product.card_button_link or old_product.live_preview_link
    else:
        custom_btn_text = None
        custom_btn_url = None

    # Creator
    creator_id = _get_creator_id(old_product, pb_session)

    # formats
    if old_product.format_ids:
        formats = get_format_str(old_product.format_ids)
    elif old_product.features_short:
        for f in old_product.features_short:
            if 'format' in f.title.lower():
                formats = f.value
                break
    else:
        formats = None
    #size
    if old_product.size:
        size = old_product.size
    elif old_product.features_short:
        for f in old_product.features_short:
            if 'size' in f.title.lower():
                size = f.value
                break
    else:
        size = 'unknown'

    # Categories
    category_id = old_product.category_ids[0]

    return pb_admin.schemas.NewProduct(
        title=old_product.title[:100],
        slug=old_product.slug,
        created_at=old_product.created_at,
        is_live=old_product.is_live,
        product_type=product_types[old_product.product_type],
        only_registered_download=old_product.email_download,
        creator_id=creator_id or 1,
        size=size,
        category_id=category_id,
        excerpt=old_product.short_description,
        description=old_product.description,
        price_commercial_cent=price_commercial_cent,
        price_extended_cent=price_extended_cent,
        price_commercial_sale_cent=price_commercial_sale_cent,
        price_extended_sale_cent=price_extended_sale_cent,
        thumbnail=_make_raw_img(old_product.thumbnail_retina if old_product.thumbnail_retina else old_product.thumbnail, pb_session),
        push_image=_make_raw_img(old_product.push_image, pb_session) if old_product.push_image else None,
        tags_ids=old_product.tags_ids,
        font_ids=old_product.font_ids,
        formats=formats,
        images=[_make_raw_img(i, pb_session) for i in images],
        presentation=_make_raw_presentation(images),
        vps_path=old_product.vps_path,
        s3_path=old_product.s3_path,
        meta_title=old_product.meta_title,
        meta_description=old_product.meta_description,
        meta_keywords=old_product.meta_keywords,
        custom_url=custom_btn_url,
        custom_url_title=custom_btn_text,
    )
