from pb_pdb import (browser, db_tools, graphic_tool, schemas, space_tools,
                    uploaders, )
from loguru import logger


@logger.catch
def to_pb_freebie(product: schemas.UploadFreebie):
    db_tools.set_status(product.prefix, 'Making img urls for upload')
    product_files = space_tools.get_file_urls(product)
    db_tools.set_status(product.prefix, 'Making product urls for upload')
    product_files.product_url, product_files.product_s3_url = uploaders.pb.make_link_product_file(
        product_files.product_url,
        'freebie',
        product.prefix
    )
    db_tools.set_status(product.prefix, 'Image preparing')
    product_files = graphic_tool.prepare_imgs(product, product_files)
    with browser.Browser() as chrome:
        driver = chrome.driver
        db_tools.set_status(product.prefix, 'Uploading to PB')
        uploaders.pb.freebie(driver, product, product_files)
    db_tools.set_status(product.prefix, 'Uploaded to PB')


@logger.catch
def to_pb_plus(product: schemas.UploadPlus):
    db_tools.set_status(product.prefix, 'Making img urls for upload')
    product_files = space_tools.get_file_urls(product)
    db_tools.set_status(product.prefix, 'Making product urls for upload')
    product_files.product_url, product_files.product_s3_url = uploaders.pb.make_link_product_file(
        product_files.product_url,
        'plus',
        product.prefix,
    )
    db_tools.set_status(product.prefix, 'Image preparing')
    product_files = graphic_tool.prepare_imgs(product, product_files)
    with browser.Browser() as chrome:
        driver = chrome.driver
        db_tools.set_status(product.prefix, 'Uploading to PB')
        uploaders.pb.plus(driver, product, product_files)
    db_tools.set_status(product.prefix, 'Uploaded to PB')


@logger.catch
def to_pb_prem(product: schemas.UploadPrem):
    db_tools.set_status(product.prefix, 'Making img urls for upload')
    product_files = space_tools.get_file_urls(product)
    db_tools.set_status(product.prefix, 'Making product urls for upload')
    product_files.product_url, product_files.product_s3_url = uploaders.pb.make_link_product_file(
        product_files.product_url,
        'premium',
        product.prefix
    )
    db_tools.set_status(product.prefix, 'Image preparing')
    product_files = graphic_tool.prepare_imgs(product, product_files)
    with browser.Browser() as chrome:
        driver = chrome.driver
        db_tools.set_status(product.prefix, 'Uploading to PB')
        uploaders.pb.prem(driver, product, product_files)
    db_tools.set_status(product.prefix, 'Uploaded to PB')


@logger.catch
def make_live(edit_link: str):
    with browser.Browser() as chrome:
        driver = chrome.driver
        uploaders.pb.make_live(driver, edit_link)