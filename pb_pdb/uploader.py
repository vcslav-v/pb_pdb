from pb_pdb import (browser, db_tools, graphic_tool, schemas, space_tools,
                    uploaders, pb_tools)
from loguru import logger
from selenium import webdriver
import os


@logger.catch
def to_pb(
    product: schemas.UploadFreebie | schemas.UploadPlus | schemas.UploadPrem,
):
    db_tools.set_status(product.prefix, 'Making img urls for upload')
    product_files = space_tools.get_file_urls(product)
    db_tools.set_status(product.prefix, 'Making product urls for upload')

    if isinstance(product, schemas.UploadFreebie):
        _pr_type = 'freebie'
    elif isinstance(product, schemas.UploadPlus):
        _pr_type = 'plus'
    elif isinstance(product, schemas.UploadPrem):
        _pr_type = 'premium'
    else:
        raise ValueError('Unknown product type')
    product_files.product_url, product_files.product_s3_url = uploaders.pb.make_link_product_file(
        product_files.product_url,
        _pr_type,
        product.prefix
    )
    db_tools.set_status(product.prefix, 'Uploading to PB')
    uploaders.pb.upload_product(product, product_files)
    db_tools.set_status(product.prefix, 'Uploaded to PB')


@logger.catch
def make_live(edit_link: str):
    uploaders.pb.make_live(edit_link)
