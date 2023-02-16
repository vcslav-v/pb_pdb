import os
from time import sleep
from urllib.parse import unquote, urlparse

from loguru import logger
import requests
import json
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from pb_pdb import schemas

LOGIN_PB = os.environ.get('LOGIN_PB', '')
PASS_PB = os.environ.get('PASS_PB', '')
PB_UPL_API_LOGIN = os.environ.get('PB_UPL_API_LOGIN', '')
PB_UPL_API_PASS = os.environ.get('PB_UPL_API_PASS', '')
PB_UPL_API_URL = os.environ.get('PB_UPL_API_URL', '')
ADMIN_PB_URL = os.environ.get('ADMIN_PB_URL', '')
PB_NEW_FREEBIE_URL = os.environ.get('PB_NEW_FREEBIE_URL', '')
PB_NEW_PLUS_URL = os.environ.get('PB_NEW_PLUS_URL', '')


def make_link_product_file(product_url: str, product_type: str):
    with requests.sessions.Session() as session:
        product = product_url.split('?')[0]
        data = {
            'upload': product,
            'type': product_type,
            'load_to_s3': False if product_type == 'freebie' else True,
            'callback': ''
    }
        session.auth = (PB_UPL_API_LOGIN, PB_UPL_API_PASS)
        resp = session.post(PB_UPL_API_URL, json=data)
        resp.raise_for_status()
        result = json.loads(resp.content)
        if not result['success']:
            raise ValueError("Can't upload to pb")
        return (result['local_link'], result['s3_link'] if result['s3_link'] else None)


def send_source_html_to_wysiwyg(driver: Remote, xpath_view: str, source_html: str):
    area_view_button = driver.find_element(By.XPATH, xpath_view)
    area_view_button.click()
    source_code_menu_item = driver.find_element(By.XPATH, '//div[@title="Source code"][@role="menuitem"]')
    source_code_menu_item.click()
    text_area = driver.find_element(By.XPATH, '//textarea[@class="tox-textarea"]')
    text_area.send_keys(source_html)
    save_button = driver.find_element(By.XPATH, '//button[@title="Save"]')
    save_button.click()

def download_to_selenium(driver: Remote, link: str) -> str:
    driver.execute_script(f'''
        var anchor = document.createElement("a");
        anchor.href = "{link}"
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
    ''')
    sleep(1)
    return f'/home/selenium/Downloads/{unquote(urlparse(link).path.split("/")[-1])}'

def login(driver: Remote):
    driver.get(ADMIN_PB_URL)

    input_email = driver.find_element(By.XPATH, '//input[@type="email"]')
    input_email.send_keys(LOGIN_PB)

    input_pass = driver.find_element(By.XPATH, '//input[@type="password"]')
    input_pass.send_keys(PASS_PB)

    submit_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    submit_button.click()

def freebie_plus_main_tab(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles, base_url: str, is_freebie=True):
    driver.get(f'{base_url}#main')
    input_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'title')
    )
    input_title.send_keys(product.title)

    input_slug = driver.find_element(By.ID, 'slug')
    input_slug.click()
    input_slug.clear()
    input_slug.send_keys(product.slug)

    input_date = driver.find_element(By.XPATH, '//input[@name="Date"]/../input[@type="text"]')
    input_date.send_keys(f'{product.date_upload.year}-{product.date_upload.month}-{product.date_upload.day}')

    status_select = driver.find_element(By.ID, 'status')
    select_status_element = Select(status_select)
    select_status_element.select_by_visible_text('Draft')

    short_desc_area = driver.find_element(By.ID, 'short_description')
    short_desc_area.send_keys(product.excerpt)

    send_source_html_to_wysiwyg(
        driver,
        '//section[@id="main"]//textarea[@id="description"]/..//button/span[text()="View"]',
        product.description,
    )

    input_size = driver.find_element(By.ID, 'size')
    input_size = input_size.send_keys(product.size)

    if is_freebie and product.download_by_email:
        check_email = driver.find_element(By.ID, 'email_download')
        check_email.click()

    input_image = driver.find_element(By.ID, '__media__material_image')
    input_image.send_keys(download_to_selenium(driver, product_files.thumbnail_url))

    input_image_retina = driver.find_element(By.ID, '__media__material_image_retina')
    input_image_retina.send_keys(download_to_selenium(driver, product_files.thumbnail_x2_url))

    input_image_push = driver.find_element(By.ID, '__media__push_image')
    input_image_push.send_keys(download_to_selenium(driver, product_files.push_url))

def freebie_plus_files_tab(driver: Remote, product_files: schemas.ProductFiles, base_url: str):
    driver.get(f'{base_url}#files')
    input_local = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'vps_path')
    )
    input_local.send_keys(product_files.product_url)

    if product_files.product_s3_url:
        input_s3 = driver.find_element(By.ID, 's3_path')
        input_s3.send_keys(product_files.product_url)

def freebie_plus_images_tab(driver: Remote, product_files: schemas.ProductFiles, base_url: str):
    driver.get(f'{base_url}#single-page-(images)')

    input_single_image = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.ID, '__media__single_image')
        )
    input_single_image.send_keys(download_to_selenium(driver, product_files.main_img_url))

    input_photo_gallery = driver.find_element(By.ID, '__media__photo_gallery_2')
    for gallery_img in product_files.gallery_urls:
        input_photo_gallery.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))

def freebie_plus_retina_images_tab(driver: Remote, product_files: schemas.ProductFiles, base_url: str):
    driver.get(f'{base_url}#single-page-(images-retina)')

    input_single_image = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.ID, '__media__single_image_retina')
        )
    input_single_image.send_keys(download_to_selenium(driver, product_files.main_img_x2_url))

    input_photo_gallery = driver.find_element(By.ID, '__media__photo_gallery_2_retina')
    for gallery_img in product_files.gallery_x2_urls:
        input_photo_gallery.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))
    
def freebie_guest_authtor(driver: Remote, product: schemas.UploadFreebie):
    driver.get(f'{PB_NEW_FREEBIE_URL}#single-page-text')
    input_author_name = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'author_name')
    )
    input_author_name.send_keys(product.guest_author)
    
    input_authtor_url = driver.find_element(By.ID, 'author_link')
    input_authtor_url.send_keys(product.guest_author_link)

def plus_guest_authtor(driver: Remote, product: schemas.UploadFreebie):
    driver.get(f'{PB_NEW_PLUS_URL}#single-page-(text)')
    input_author_name = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'author_name')
    )
    input_author_name.send_keys(product.guest_author)
    
    input_authtor_url = driver.find_element(By.ID, 'author_link')
    input_authtor_url.send_keys(product.guest_author_link)

def freebie_plus_categories(driver: Remote, product: schemas.UploadFreebie, base_url: str):
    driver.get(f'{base_url}#categories')

    for category in product.categories:
        category_checkbox = WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.XPATH, f'//section[@id="categories"]//p[text()="{category}"]/../..')
            )
        category_checkbox.click()

def freebie_plus_formats(driver: Remote, product: schemas.UploadFreebie, base_url: str):
    driver.get(f'{base_url}#formats')

    for product_format in product.formats:
        format_checkbox = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, f'//section[@id="formats"]//p[text()="{product_format}"]/../..')
        )
        format_checkbox.click()

def freebie_plus_metatags(driver: Remote, product: schemas.UploadFreebie, base_url: str):
    driver.get(f'{base_url}#meta-tags')

    input_meta_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'meta_title')
    )
    input_meta_title.send_keys(product.meta_title)

    input_meta_desc = driver.find_element(By.ID, 'meta_description')
    input_meta_desc.send_keys(product.meta_description)

def freebie_submit(driver: Remote, product: schemas.UploadFreebie):
    button_submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
    button_submit.click()
    sleep(5)
    # TODO вернуть чек как починят
    # WebDriverWait(driver, timeout=40).until(
    #     lambda d: d.find_element(By.XPATH, f'//h1[text()="Freeby Details: {product.title}"]')
    # )


def plus_submit(driver: Remote, product: schemas.UploadFreebie):
    button_submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
    button_submit.click()
    sleep(5)
    # TODO вернуть чек как починят + проверить этот чек
    # WebDriverWait(driver, timeout=40).until(
    #     lambda d: d.find_element(By.XPATH, f'//h1[text()="Plus Details: {product.title}"]')
    # )

def new_freebie(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    logger.debug('get new freebie page')
    driver.get(PB_NEW_FREEBIE_URL)
    logger.debug('main freebie page')
    freebie_plus_main_tab(driver, product, product_files, PB_NEW_FREEBIE_URL)
    logger.debug('files freebie page')
    freebie_plus_files_tab(driver, product_files, PB_NEW_FREEBIE_URL)
    logger.debug('images freebie page')
    freebie_plus_images_tab(driver, product_files, PB_NEW_FREEBIE_URL)
    logger.debug('retina images freebie page')
    freebie_plus_retina_images_tab(driver, product_files, PB_NEW_FREEBIE_URL)
    if product.guest_author and product.guest_author_link:
        logger.debug('make guest authtor')
        freebie_guest_authtor(driver, product)
    logger.debug('categories freebie page')
    freebie_plus_categories(driver, product, PB_NEW_FREEBIE_URL)
    logger.debug('formats freebie page')
    freebie_plus_formats(driver, product, PB_NEW_FREEBIE_URL)
    logger.debug('metatags freebie page')
    freebie_plus_metatags(driver, product, PB_NEW_FREEBIE_URL)
    logger.debug('freebie submit')
    freebie_submit(driver, product)

def new_plus(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    logger.debug('get new plus page')
    driver.get(PB_NEW_PLUS_URL)
    logger.debug('main plus page')
    freebie_plus_main_tab(driver, product, product_files, PB_NEW_PLUS_URL, is_freebie=False)
    logger.debug('files plus page')
    freebie_plus_files_tab(driver, product_files, PB_NEW_PLUS_URL)
    logger.debug('images plus page')
    freebie_plus_images_tab(driver, product_files, PB_NEW_PLUS_URL)
    logger.debug('retina images plus page')
    freebie_plus_retina_images_tab(driver, product_files, PB_NEW_PLUS_URL)
    if product.guest_author and product.guest_author_link:
        logger.debug('make guest authtor')
        plus_guest_authtor(driver, product)
    logger.debug('categories plus page')
    freebie_plus_categories(driver, product, PB_NEW_PLUS_URL)
    logger.debug('formats plus page')
    freebie_plus_formats(driver, product, PB_NEW_PLUS_URL)
    logger.debug('metatags plus page')
    freebie_plus_metatags(driver, product, PB_NEW_PLUS_URL)
    logger.debug('plus submit')
    plus_submit(driver, product)


def freebie(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    login(driver)
    new_freebie(driver, product, product_files)


def plus(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    login(driver)
    new_plus(driver, product, product_files)
