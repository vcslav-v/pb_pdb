import os
from time import sleep
from urllib.parse import unquote, urlparse

import requests

from loguru import logger
from datetime import datetime


from pb_admin import schemas as pb_schemas
from pb_pdb import schemas, db_tools, pb_tools

LOGIN_PB = os.environ.get('LOGIN_PB', '')
PASS_PB = os.environ.get('PASS_PB', '')
PB_UPL_API_LOGIN = os.environ.get('PB_UPL_API_LOGIN', '')
PB_UPL_API_PASS = os.environ.get('PB_UPL_API_PASS', '')
PB_UPL_API_URL = os.environ.get('PB_UPL_API_URL', '')
ADMIN_PB_URL = os.environ.get('ADMIN_PB_URL', '')
PB_NEW_FREEBIE_URL = os.environ.get('PB_NEW_FREEBIE_URL', '')
PB_NEW_PLUS_URL = os.environ.get('PB_NEW_PLUS_URL', '')
PB_NEW_PREM_URL = os.environ.get('PB_NEW_PREM_URL', '')
PB_LIST_FREEBIE_URL = os.environ.get('PB_LIST_FREEBIE_URL', '')
PB_LIST_PLUS_URL = os.environ.get('PB_LIST_PLUS_URL', '')
PB_LIST_PREM_URL = os.environ.get('PB_LIST_PREM_URL', '')
PB_EDIT_FREEBIE_URL = os.environ.get('PB_EDIT_FREEBIE_URL', '')
PB_EDIT_PLUS_URL = os.environ.get('PB_EDIT_PLUS_URL', '')
PB_EDIT_PREM_URL = os.environ.get('PB_EDIT_PREM_URL', '')
CALL_BACK_URL = os.environ.get('CALL_BACK_URL', '')


def make_link_product_file(product_url: str, product_type: str, prefix: str):
    with requests.sessions.Session() as session:
        product = product_url.split('?')[0]
        data = {
            'upload': product,
            'type': product_type,
            'load_to_s3': True,
            'callback': CALL_BACK_URL.format(prefix=prefix)
        }
        logger.debug(data)
        session.auth = (PB_UPL_API_LOGIN, PB_UPL_API_PASS)
        resp = session.post(PB_UPL_API_URL, json=data)
        resp.raise_for_status()
        result = db_tools.get_callback_data(prefix)
        while not result:
            sleep(5)
            result = db_tools.get_callback_data(prefix)
        db_tools.rm_callback(prefix)
        result = schemas.UploaderResponse.parse_raw(result)
        return (result.local_link, result.s3_link if result.s3_link else None)


def upload_product(
        product: schemas.UploadFreebie | schemas.UploadPlus | schemas.UploadPrem,
        product_files: schemas.ProductFiles
):
    new_product: pb_schemas.NewProduct = pb_tools.upload_product(product, product_files)
    if product.schedule_date and datetime.utcnow().timestamp() < product.schedule_date.timestamp():
        db_tools.set_status(product.prefix, 'Set product schedule')
        db_tools.add_to_product_schedule(
            product.schedule_date,
            PB_EDIT_URL.format(pr_id=new_product.ident),
            product.title,
        )


def make_live(edit_link: str):
    parsed_url = urlparse(edit_link)

    product_id = unquote(parsed_url.path.split('/')[-2])
    if product_id.isdigit():
        product_id = int(product_id)
    else:
        raise ValueError('Wrong product id')

    pb_tools.make_life(product_id)
