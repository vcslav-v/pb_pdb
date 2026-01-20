import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger
from pb_pdb import schemas, trello_tools, db_tools, bq_tools
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


@router.get('/product_img/{product_id}')
def get_product_img(product_id: int):
    headers = {
        'Content-Type': 'image/jpeg',
    }
    return Response(db_tools.get_product_img(product_id), headers=headers)


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
def publish(card_id: str):
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
def pb_freebie_upload(
    freebie_product: schemas.UploadFreebie,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_username)
):
    logger.debug(freebie_product)
    background_tasks.add_task(service.upload_product, freebie_product, 'pb', 'freebie')


@router.post('/pb_plus_upload')
@logger.catch
def pb_plus_upload(
    plus_product: schemas.UploadPlus,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_username)
):
    logger.debug(plus_product)
    background_tasks.add_task(service.upload_product, plus_product, 'pb', 'plus')


@router.post('/pb_prem_upload')
@logger.catch
def pb_prem_upload(
    prem_product: schemas.UploadPrem,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_username)
):
    logger.debug(prem_product)
    background_tasks.add_task(service.upload_product, prem_product, 'pb', 'prem')


@router.post('/get_status_upload')
@logger.catch
def get_status_upload(prefix, _: str = Depends(get_current_username)):
    return db_tools.get_status(prefix)


@router.post('/push_uploader_links/{prefix}')
@logger.catch
def push_uploader_links(prefix: str, uploader_resp: schemas.UploaderResponse):
    db_tools.set_uploader_callback(uploader_resp, prefix)


@router.post('/rm_task/{ident}')
@logger.catch
def rm_task(ident: int, _: str = Depends(get_current_username)):
    db_tools.rm_product_schedule(ident)


@router.post('/update_date_task/{ident}')
@logger.catch
def update_date_task(
    ident: int,
    schedule: schemas.ScheduleUpdate,
    _: str = Depends(get_current_username)
):
    db_tools.update_product_schedule(ident, schedule.date_time)


@router.post('/get_product_schedule')
@logger.catch
def get_product_schedule(_: str = Depends(get_current_username)):
    db_result = db_tools.get_product_schedule()
    result = schemas.PageProductsSchedule(
        page=[schemas.ProductsSchedule(
            ident=task.id,
            name=task.name,
            edit_link=task.edit_url,
            date_time=task.date_time,
        ) for task in db_result]
    )
    return result


@router.post('/set_bulk_tag')
@logger.catch
def set_bulk_tag(
    data: schemas.BulkTag,
    _: str = Depends(get_current_username)
):
    db_tools.set_bulk_tag_task(data)


@router.get('/bulk_tag_count_tasks')
@logger.catch
def bulk_tag_count_tasks(
    _: str = Depends(get_current_username)
) -> int:
    return db_tools.get_bulk_tag_count_tasks()

@router.post('/sync_bq')
@logger.catch
def sync_bq(
    _: str = Depends(get_current_username)
):
    bq_tools.sync()


@router.get("/trello_product/img/{trello_card_id}.jpg")
@logger.catch
def get_trello_product_img(trello_card_id: str):
    img_bytes = db_tools.get_trello_cover(trello_card_id)

    if not img_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return Response(
        content=img_bytes,
        media_type="image/jpeg",
    )