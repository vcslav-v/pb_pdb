import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger
from pb_pdb import schemas, trello_tools, db_tools
from pb_pdb.api import service

router = APIRouter()
security = HTTPBasic()

username = os.environ.get('API_USERNAME') or 'api'
password = os.environ.get('API_PASSWORD') or 'pass'


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return credentials.username


@router.get('/stest')
def stest(_: str = Depends(get_current_username)):
    return 'test-test'


@router.get('/add_trello_product')
@logger.catch
def add_trello_product(card_id: str):
    try:
        name = trello_tools.add_trello_product(card_id)
    except ValueError as e:
        name = e.args[0]
    return schemas.TrelloProduct(name=name)


@router.get('/make_subproduct_name')
@logger.catch
def make_subproduct_name(card_id: str):
    name = trello_tools.make_subproduct(card_id)
    logger.debug(name)
    return schemas.TrelloProduct(name=name)


@router.get('/make_final_text')
@logger.catch
def make_final_text(card_id: str):
    trello_tools.make_final_text(card_id)


@router.get('/publish')
@logger.catch
def make_final_text(card_id: str):
    trello_tools.publish(card_id)


@router.get('/production_end')
@logger.catch
def production_end(card_id: str):
    db_tools.production_end(card_id)


@router.post('/products')
@logger.catch
def get_products(filter_data: schemas.FilterPage) -> schemas.ProductPage:
    products = db_tools.get_products(filter_data)
    return products

@router.get('/common_data')
@logger.catch
def get_common_data() -> schemas.ProductPageData:
    page = db_tools.get_common_data()
    return page


@router.post('/pb_freebie_upload')
@logger.catch
def pb_freebie_upload(freebie_product: schemas.UploadFreebie, background_tasks: BackgroundTasks, _: str = Depends(get_current_username)):
    background_tasks.add_task(service.upload_product, freebie_product, 'pb', 'freebie')

@router.post('/pb_plus_upload')
@logger.catch
def pb_plus_upload(plus_product: schemas.UploadPlus, background_tasks: BackgroundTasks, _: str = Depends(get_current_username)):
    background_tasks.add_task(service.upload_product, plus_product, 'pb', 'plus')

@router.post('/pb_prem_upload')
@logger.catch
def pb_prem_upload(prem_product: schemas.UploadPrem, background_tasks: BackgroundTasks, _: str = Depends(get_current_username)):
    background_tasks.add_task(service.upload_product, prem_product, 'pb', 'prem')



@router.post('/get_status_upload')
@logger.catch
def get_status_upload(prefix, _: str = Depends(get_current_username)):
    return db_tools.get_status(prefix)


@router.post('/push_uploader_links/{prefix}')
@logger.catch
async def push_uploader_links(prefix: str, request: Request):#uploader_resp: schemas.UploaderResponse):
    logger.debug(prefix)
    logger.debug(await request.body())
    return request.json
