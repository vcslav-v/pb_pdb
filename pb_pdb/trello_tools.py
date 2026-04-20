import json
import os
import re
from typing import Optional
from urllib.parse import urlparse

import requests
from trello import TrelloApi

from pb_pdb import config, db_tools, schemas
from loguru import logger

from datetime import datetime

TRELLO_AUTH_KEY = os.environ.get(
    'TRELLO_AUTH_KEY',
    '',
)
TRELLO_APP_KEY = os.environ.get('TRELLO_APP_KEY', '')
BIG_PRODUCT_LABEL = os.environ.get('BIG_PRODUCT_LABEL', 'The big product')
EXTRA_PRODUCT_LABEL = os.environ.get('EXTRA_PRODUCT_LABEL', 'Extra product')
END_PRODUCTION_LIST = os.environ.get('END_PRODUCTION_LIST', 'Title, Description')

def _parse_int_list(s: str) -> list[int]:
    if not s:
        return []
    return [int(x) for x in re.findall(r"-?\d+", s)]


def _trello_get(path, **params):
    r = requests.get(
        f"https://api.trello.com/1{path}",
        params={"key": TRELLO_APP_KEY, "token": TRELLO_AUTH_KEY, **params},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def _get_card_custom_fields(card_id: str) -> dict:
    card = _trello_get(f"/cards/{card_id}", fields="idBoard")
    board_id = card["idBoard"]

    board_fields = _trello_get(f"/boards/{board_id}/customFields")
    field_by_id = {f["id"]: f for f in board_fields}

    options_by_field = {}
    for f in board_fields:
        if f.get("type") == "list":
            options_by_field[f["id"]] = {o["id"]: o["value"]["text"] for o in f.get("options", [])}

    items = _trello_get(f"/cards/{card_id}/customFieldItems")

    result = {}
    for it in items:
        fid = it["idCustomField"]
        fdef = field_by_id.get(fid)
        if not fdef:
            continue

        name = fdef.get("name", fid)
        ftype = fdef.get("type")

        if ftype == "list":  # dropdown
            id_value = it.get("idValue")
            result[name] = options_by_field.get(fid, {}).get(id_value, id_value)
        else:
            v = it.get("value") or {}
            result[name] = v.get("text") or v.get("number") or v.get("date") or v.get("checked")

    return result



def get_dropbox_link_from_attachs(attachs: list[dict]) -> Optional[str]:
    for attach in attachs:
        if 'dropbox.com' in urlparse(attach['url']).netloc:
            return attach['id']


def download_pic(url: str) -> bytes:
    resp = requests.get(url)
    if resp.ok:
        return resp.content


def get_full_name(name: str) -> tuple[str]:
    raw_name = name.split(' - ')
    name = raw_name[-1]
    own_id = ''
    parrent_uid = ''
    if len(raw_name) > 1:
        id_area = raw_name[0]
        parrent_uid = re.findall(r'(?<=\().*(?=\))', id_area)
        parrent_uid = parrent_uid[0] if parrent_uid else ''
        own_id = re.findall(r'(?<!\()\w+\d(?!\))', id_area)
        own_id = own_id[0] if own_id else ''
    return own_id, parrent_uid, name


def get_parrent_product(attachs: list[dict], trello: TrelloApi) -> str:
    short_link_cards = []
    for attach in attachs:
        is_trello_url = 'trello.com' in urlparse(attach['url']).netloc
        short_link_card = re.findall(r'(?<=/c/).*', attach['url'])
        if is_trello_url and short_link_card:
            short_link_cards.append(short_link_card[0])

    for short_link_card in short_link_cards:
        card = trello.cards.get(short_link_card)
        _own_id, parrent_uid, _work_title = get_full_name(card['name'])
        if parrent_uid:
            continue
        return card['id']


def add_trello_product(card_id: str):
    trello = TrelloApi(TRELLO_APP_KEY)
    trello.set_token(TRELLO_AUTH_KEY)
    product_card = trello.cards.get(card_id)
    _own_id, _parrent_uid, work_title = get_full_name(product_card['name'])
    labels = [label['name'] for label in product_card['labels']]
    is_big_product = BIG_PRODUCT_LABEL in labels
    is_extra_product = EXTRA_PRODUCT_LABEL in labels
    category = db_tools.get_exist_category_from_list(labels)
    if not category:
        raise ValueError(f'ERROR Wrong category label - {work_title}')
    description = product_card['desc']
    card_attachs = trello.cards.get_attachment(card_id)
    dropbox_attch_id = get_dropbox_link_from_attachs(card_attachs)
    if dropbox_attch_id:
        trello.cards.delete_attachment_idAttachment(dropbox_attch_id, card_id)
    parrent_product = get_parrent_product(card_attachs, trello)
    designer_id = product_card['idMembers'][0]
    trello_member = trello.members.get(designer_id)
    designer_full_name = trello_member['fullName']
    url_designer_user_pick = trello_member['avatarUrl']
    user_pick = download_pic(f'{url_designer_user_pick}/60.png')

    new_product = schemas.Product(
        trello_card_id=card_id,
        trello_link=product_card['url'],
        title=work_title,
        description=description,
        category=category,
        parrent_id=parrent_product,
        is_big_product=is_big_product,
        is_extra_product=is_extra_product,
    )

    designer = schemas.Employee(
        full_name=designer_full_name,
        trello_id=designer_id,
        user_pick=user_pick,
    )

    full_product_name, share_link = db_tools.add_product(new_product, designer)
    trello.cards.new_attachment(card_id, url=share_link)

    return full_product_name


def make_subproduct(card_id: str) -> str:
    trello = TrelloApi(TRELLO_APP_KEY)
    trello.set_token(TRELLO_AUTH_KEY)
    product_card = trello.cards.get(card_id)
    parrent_uid, _, work_title = get_full_name(product_card['name'])
    product_name = f'({parrent_uid}) - {work_title}' if parrent_uid else work_title

    card_attachs = trello.cards.get_attachment(card_id)

    short_link_cards = []
    for attach in card_attachs:
        is_trello_url = 'trello.com' in urlparse(attach['url']).netloc
        short_link_card = re.findall(r'(?<=/c/).*', attach['url'])
        if is_trello_url and short_link_card:
            short_link_cards.append((short_link_card[0], attach['id']))
        else:
            trello.cards.delete_attachment_idAttachment(attach['id'], card_id)

    for short_link_card, attach_id in short_link_cards:
        card = trello.cards.get(short_link_card)
        _, parrent_uid, _ = get_full_name(card['name'])
        if parrent_uid:
            trello.cards.delete_attachment_idAttachment(attach_id, card_id)

    return product_name


def make_final_text(card_id: str):
    trello = TrelloApi(TRELLO_APP_KEY)
    trello.set_token(TRELLO_AUTH_KEY)
    product_card = trello.cards.get(card_id)
    labels = [label['name'] for label in product_card['labels']]
    is_big_product = BIG_PRODUCT_LABEL in labels
    is_extra_product = EXTRA_PRODUCT_LABEL in labels
    description = product_card['desc']
    own_id, parrent_uid, title = get_full_name(product_card['name'])
    db_tools.make_final_text(
        card_id,
        product_card['name'],
        title, description,
        is_big_product,
        is_extra_product
    )


def publish(card_id: str):
    logger.info(f'Publishing card {card_id}')
    trello = TrelloApi(TRELLO_APP_KEY)
    trello.set_token(TRELLO_AUTH_KEY)
    product_card = trello.cards.get(card_id)
    labels = [label['name'] for label in product_card['labels']]
    is_extra = EXTRA_PRODUCT_LABEL in labels
    custom_fields = _get_card_custom_fields(card_id)
    adobe_ids = _parse_int_list(custom_fields.get('Adobe IDs', ''))
    if custom_fields.get('Freelance Type', '').strip() and custom_fields.get('Freelance ID', '').strip():
        freelance_id = f"{custom_fields.get('Freelance Type', '')}|{custom_fields.get('Freelance ID', '')}"
    else:
        freelance_id = None
    designer_outer_id = db_tools.publish_product(card_id)
    data = schemas.TrelloCreatorProduct(
        creator_id=designer_outer_id,
        freelance_id=freelance_id,
        product_ids=adobe_ids,
        is_extra=is_extra,
    )
    response = requests.post(f'{config.ADOBE_PARSER_API_URL}/api/update_trello_creator_product',
        data=data.model_dump_json(),
        auth=(config.ADOBE_PARSER_API_LOGIN, config.ADOBE_PARSER_API_PASSWORD),
        timeout=30
    )
    logger.info(f'Publish response: {response.status_code} {response.text}')


def get_end_production_date(card_id):
    trello = TrelloApi(TRELLO_APP_KEY)
    trello.set_token(TRELLO_AUTH_KEY)
    try:
        card_actions = trello.cards.get_action(card_id)
    except:
        return None
    for action in card_actions:
        if action['type'] == 'updateCard' and action['data']['listAfter']['name'] == END_PRODUCTION_LIST:
            break
    else:
        return None
    return datetime.fromisoformat(action['date']).date()
