import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger
from pb_pdb import schemas, trello_tools

router = APIRouter()
security = HTTPBasic()

username = os.environ.get('API_USERNAME') or 'root'
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
