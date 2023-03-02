import os
from time import sleep
from urllib.parse import unquote, urlparse

from loguru import logger
import requests
import json
from selenium.webdriver import Remote, ActionChains
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
PB_NEW_PREM_URL = os.environ.get('PB_NEW_PREM_URL', '')
PB_LIST_FREEBIE_URL = os.environ.get('PB_NEW_FREEBIE_URL', '')
PB_LIST_PLUS_URL = os.environ.get('PB_NEW_PLUS_URL', '')
PB_LIST_PREM_URL = os.environ.get('PB_NEW_PREM_URL', '')


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
    driver.get(f'{base_url}?tab=main')
    input_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'title')
    )
    input_title.send_keys(product.title)

    input_slug = driver.find_element(By.ID, 'slug')
    input_slug.click()
    input_slug.clear()
    input_slug.send_keys(product.slug)

    input_date = driver.find_element(By.XPATH, '//input[@name="Date"]/../input[@type="text"]')
    input_date.send_keys(product.date_upload.strftime('%Y-%m-%d %H:%M:%S'))

    status_select = driver.find_element(By.ID, 'status')
    select_status_element = Select(status_select)
    select_status_element.select_by_visible_text('Live')

    short_desc_area = driver.find_element(By.ID, 'short_description')
    short_desc_area.send_keys(product.excerpt)

    send_source_html_to_wysiwyg(
        driver,
        '//div[@label="Main"]//textarea[@id="description"]/..//button/span[text()="View"]',
        product.description,
    )

    input_size = driver.find_element(By.ID, 'size')
    input_size = input_size.send_keys(product.size)

    if is_freebie:
        check_statistic = driver.find_element(By.ID, 'show_stats')
        check_statistic.click()

        input_count = driver.find_element(By.ID, 'count_downloads')
        input_count.send_keys('3')

    if is_freebie and product.download_by_email:
        check_email = driver.find_element(By.ID, 'email_download')
        check_email.click()

    input_image = driver.find_element(By.ID, '__media__material_image')
    input_image.send_keys(download_to_selenium(driver, product_files.thumbnail_url))

    input_image_retina = driver.find_element(By.ID, '__media__material_image_retina')
    input_image_retina.send_keys(download_to_selenium(driver, product_files.thumbnail_x2_url))

    input_image_push = driver.find_element(By.ID, '__media__push_image')
    input_image_push.send_keys(download_to_selenium(driver, product_files.push_url))

    make_alt_img(driver, product, 'Main')

def prem_main_tab(driver, product: schemas.UploadPrem, product_files: schemas.ProductFiles, base_url: str):
    driver.get(f'{base_url}?tab=main')
    input_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'title')
    )
    input_title.send_keys(product.title)

    input_slug = driver.find_element(By.ID, 'slug')
    input_slug.click()
    input_slug.clear()
    input_slug.send_keys(product.slug)

    input_date = driver.find_element(By.XPATH, '//input[@name="Date"]/../input[@type="text"]')
    input_date.send_keys(product.date_upload.strftime('%Y-%m-%d %H:%M:%S'))

    status_select = driver.find_element(By.ID, 'status')
    select_status_element = Select(status_select)
    select_status_element.select_by_visible_text('Live')

    short_desc_area = driver.find_element(By.ID, 'short_description')
    short_desc_area.send_keys(product.excerpt)
    
    if product.sale_standart_price is not None:
        input_std_price = driver.find_element(By.ID, 'price_standard')
        input_std_price.send_keys(product.sale_standart_price)
        input_std_price_old = driver.find_element(By.ID, 'price_standard_old')
        input_std_price_old.send_keys(product.standart_price)
    else:
        input_std_price = driver.find_element(By.ID, 'price_standard')
        input_std_price.send_keys(product.standart_price)
    
    if product.sale_extended_price is not None:
        input_ext_price = driver.find_element(By.ID, 'price_extended')
        input_ext_price.send_keys(product.sale_extended_price)
        input_ext_price_old = driver.find_element(By.ID, 'price_extended_old')
        input_ext_price_old.send_keys(product.extended_price)
    else:
        input_ext_price = driver.find_element(By.ID, 'price_extended')
        input_ext_price.send_keys(product.extended_price)
    

    input_image = driver.find_element(By.ID, '__media__material_image')
    input_image.send_keys(download_to_selenium(driver, product_files.thumbnail_url))

    input_image_retina = driver.find_element(By.ID, '__media__material_image_retina')
    input_image_retina.send_keys(download_to_selenium(driver, product_files.thumbnail_x2_url))
    
    input_image_catalog = driver.find_element(By.ID, '__media__material_image_for_catalog')
    input_image_catalog.send_keys(download_to_selenium(driver, product_files.prem_thumbnail_url))
    
    input_image_retina_catalog = driver.find_element(By.ID, '__media__material_image_retina_for_catalog')
    input_image_retina_catalog.send_keys(download_to_selenium(driver, product_files.prem_thumbnail_x2_url))

    input_image_push = driver.find_element(By.ID, '__media__push_image')
    input_image_push.send_keys(download_to_selenium(driver, product_files.push_url))
    make_alt_img(driver, product, 'Main')

def files_tab(driver: Remote, product_files: schemas.ProductFiles):
    tab = driver.find_element(By.XPATH, '//div[@dusk="files-tab"]')
    tab.click()
    input_local = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'vps_path')
    )
    input_local.send_keys(urlparse(product_files.product_url).path.strip('/'))

    if product_files.product_s3_url:
        input_s3 = driver.find_element(By.ID, 's3_path')
        input_s3.send_keys(urlparse(product_files.product_s3_url).path.strip('/'))

def freebie_plus_images_tab(driver: Remote, product_files: schemas.ProductFiles, product: schemas.UploadProduct):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-images-tab"]')
    tab.click()

    input_single_image = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.ID, '__media__single_image')
        )
    input_single_image.send_keys(download_to_selenium(driver, product_files.main_img_url))

    input_photo_gallery = driver.find_element(By.ID, '__media__photo_gallery_2')
    for gallery_img in product_files.gallery_urls:
        input_photo_gallery.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))
    make_alt_img(driver, product, 'Single Page (images)')

def prem_images_tab(driver, product_files: schemas.ProductFiles, product: schemas.UploadPrem):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-images-tab"]')
    tab.click()

    input_premium_main = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.ID, '__media__premium_main')
        )
    input_premium_main.send_keys(download_to_selenium(driver, product_files.main_img_url))
    
    input_premium_main_x2 = driver.find_element(By.ID, '__media__premium_main_retina')
    input_premium_main_x2.send_keys(download_to_selenium(driver, product_files.main_img_x2_url))
    

    input_premium_slider = driver.find_element(By.ID, '__media__premium_slider')
    for gallery_img in product_files.gallery_urls:
        input_premium_slider.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))
    
    input_premium_slider_x2 = driver.find_element(By.ID, '__media__premium_slider_retina')
    for gallery_img in product_files.gallery_x2_urls:
        input_premium_slider_x2.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))
    
    make_alt_img(driver, product, 'Single page (images)')

def freebie_plus_retina_images_tab(driver: Remote, product_files: schemas.ProductFiles, product: schemas.UploadProduct):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-images-retina-tab"]')
    tab.click()

    input_single_image = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.ID, '__media__single_image_retina')
        )
    input_single_image.send_keys(download_to_selenium(driver, product_files.main_img_x2_url))

    input_photo_gallery = driver.find_element(By.ID, '__media__photo_gallery_2_retina')
    for gallery_img in product_files.gallery_x2_urls:
        input_photo_gallery.send_keys(download_to_selenium(driver, gallery_img).replace('|', '_'))
    
    make_alt_img(driver, product, 'Single Page (images retina)')
    
def freebie_guest_authtor(driver: Remote, product: schemas.UploadFreebie):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-text-tab"]')
    tab.click()

    input_author_name = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'author_name')
    )
    input_author_name.send_keys(product.guest_author)
    
    input_authtor_url = driver.find_element(By.ID, 'author_link')
    input_authtor_url.send_keys(product.guest_author_link)

def prem_single_page(driver, product: schemas.UploadPrem):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-text-tab"]')
    tab.click()

    short_desc_area = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//div[@label="Single page (text)"]//textarea[@id="short_description"]')
    )
    short_desc_area.send_keys(product.excerpt)
    
    send_source_html_to_wysiwyg(
        driver,
        '//div[@label="Single page (text)"]//textarea[@id="description"]/..//button/span[text()="View"]',
        product.description,
    )

def plus_guest_authtor(driver: Remote, product: schemas.UploadFreebie):
    tab = driver.find_element(By.XPATH, '//div[@dusk="single-page-text-tab"]')
    tab.click()

    input_author_name = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'author_name')
    )
    input_author_name.send_keys(product.guest_author)
    
    input_authtor_url = driver.find_element(By.ID, 'author_link')
    input_authtor_url.send_keys(product.guest_author_link)

def set_categories(driver: Remote, product: schemas.UploadProduct):
    tab = driver.find_element(By.XPATH, '//div[@dusk="categories-tab"]')
    tab.click()

    for category in product.categories:
        category_checkbox = WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.XPATH, f'//div[@label="Categories"]//p[text()="{category}"]/../..')
            )
        category_checkbox.click()

def freebie_plus_formats(driver: Remote, product: schemas.UploadFreebie):
    tab = driver.find_element(By.XPATH, '//div[@dusk="formats-tab"]')
    tab.click()

    for product_format in product.formats:
        format_checkbox = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, f'//div[@label="Formats"]//p[text()="{product_format}"]/../..')
        )
        format_checkbox.click()

def set_prem_features(driver, product: schemas.UploadPrem):
    tab = driver.find_element(By.XPATH, '//div[@dusk="features-tab"]')
    tab.click()
    button_add_row = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//div[@label="Features"]//button[contains(.,"Add row")]')
    )
    button_add_row.click()
    input_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//div[@label="Features"]//input[@id="title"]')
    )
    input_title.send_keys('Format')
    input_value = driver.find_element(By.XPATH, '//div[@label="Features"]//input[@id="value"]')
    input_value.send_keys(', '.join(product.formats))
    
    button_add_row = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '//div[@label="Features"]//button[contains(.,"Add row")]')
    )
    button_add_row.click()
    input_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, '(//div[@label="Features"]//input[@id="title"])[2]')
    )
    input_title.send_keys('File size')
    input_value = driver.find_element(By.XPATH, '(//div[@label="Features"]//input[@id="value"])[2]')
    input_value.send_keys(product.size.upper())

def set_compatibilities(driver, product: schemas.UploadPrem):
    tab = driver.find_element(By.XPATH, '//div[@dusk="compatibilities-tab"]')
    tab.click()
    for product_compatibilities in product.compatibilities:
        compatibilities_checkbox = WebDriverWait(driver, timeout=20).until(
            lambda d: d.find_element(By.XPATH, f'//div[@label="Compatibilities"]//p[text()="{product_compatibilities}"]/../..')
        )
        compatibilities_checkbox.click()

def set_metatags(driver: Remote, product: schemas.UploadFreebie):
    tab = driver.find_element(By.XPATH, '//div[@dusk="meta-tags-tab"]')
    tab.click()

    input_meta_title = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.ID, 'meta_title')
    )
    input_meta_title.send_keys(product.meta_title)

    input_meta_desc = driver.find_element(By.ID, 'meta_description')
    input_meta_desc.send_keys(product.meta_description)


def make_alt_img(driver: Remote, product: schemas.UploadFreebie, tab_lable: str):
    images = driver.find_elements(
        By.XPATH, 
        f'//div[@label="{tab_lable}"]//div[contains(@class,"gallery-item-image")]'
    )
    button_alts = driver.find_elements(
        By.XPATH,
        '//div[@label="{tab_lable}"]//a[@title="Edit custom properties"]'
    )
    actions = ActionChains(driver)

    for image, button_alt in zip(images, button_alts):
        actions.move_to_element(image).pause(1).perform()
        button_alt.click()
    
        input_alt = WebDriverWait(driver, timeout=40).until(
            lambda d: d.find_element(By.XPATH, '//input[@id="alt"]')
        )
        input_alt.send_keys(product.meta_title)
        button_update = driver.find_element(By.XPATH, '//div[@class="action"]/..//button[@type="submit"]')
        button_update.click()
        sleep(1)


def freebie_submit(driver: Remote, product: schemas.UploadFreebie) -> str:
    button_submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
    button_submit.click()
    p_id = WebDriverWait(driver, timeout=40).until(
        lambda d: d.find_element(By.XPATH, '//div[@class="tab-content main"]//h4[contains(text(),"ID")]/../..//p')
    )
    return p_id.text.strip()


def plus_submit(driver: Remote, product: schemas.UploadPlus) -> str:
    button_submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
    button_submit.click()
    p_id = WebDriverWait(driver, timeout=40).until(
        lambda d: d.find_element(By.XPATH, '//div[@class="tab-content main"]//h4[contains(text(),"ID")]/../..//p')
    )
    return p_id.text.strip()


def prem_submit(driver: Remote, product: schemas.UploadPrem) -> str:
    button_submit = driver.find_element(By.XPATH, '//button[@type="submit"]')
    button_submit.click()
    p_id = WebDriverWait(driver, timeout=40).until(
            lambda d: d.find_element(By.XPATH, '//div[@class="tab-content main"]//h4[contains(text(),"ID")]/../..//p')
        )
    return p_id.text.strip()


@logger.catch
def make_push(driver: Remote, product_id: int, base_url: str):
    driver.get(base_url)

    check_product = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, f'//tr[@dusk="{product_id}-row"]//input')
    )
    check_product.click()

    select_action = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, f'//select[@dusk="action-select"]')
    )
    select_action_element = Select(select_action)
    select_action_element.select_by_value('send-push')
    
    action_button = driver.find_element(By.XPATH, '//button[@dusk="run-action-button"]')
    action_button.click()

    button_submit = WebDriverWait(driver, timeout=20).until(
        lambda d: d.find_element(By.XPATH, f'//button[@type="submit"]')
    )
    button_submit.click()

    WebDriverWait(driver, timeout=120).until(
        lambda d: d.find_element(By.XPATH, f'//div[@class="toasted nova success"]')
    )
    

def new_freebie(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    logger.debug('get new freebie page')
    driver.get(PB_NEW_FREEBIE_URL)
    logger.debug('main freebie page')
    freebie_plus_main_tab(driver, product, product_files, PB_NEW_FREEBIE_URL)
    logger.debug('files freebie page')
    files_tab(driver, product_files)
    logger.debug('images freebie page')
    freebie_plus_images_tab(driver, product_files, product)
    logger.debug('retina images freebie page')
    freebie_plus_retina_images_tab(driver, product_files, product)
    if product.guest_author and product.guest_author_link:
        logger.debug('make guest authtor')
        freebie_guest_authtor(driver, product)
    logger.debug('categories freebie page')
    set_categories(driver, product)
    logger.debug('formats freebie page')
    freebie_plus_formats(driver, product)
    logger.debug('metatags freebie page')
    set_metatags(driver, product)
    logger.debug('freebie submit')
    pr_id = freebie_submit(driver, product)
    logger.debug(f'pr_id={pr_id}')
    make_push(driver, pr_id, PB_LIST_FREEBIE_URL)

def new_plus(driver: Remote, product: schemas.UploadPlus, product_files: schemas.ProductFiles):
    logger.debug('get new plus page')
    driver.get(PB_NEW_PLUS_URL)
    logger.debug('main plus page')
    freebie_plus_main_tab(driver, product, product_files, PB_NEW_PLUS_URL, is_freebie=False)
    logger.debug('files plus page')
    files_tab(driver, product_files)
    logger.debug('images plus page')
    freebie_plus_images_tab(driver, product_files, product)
    logger.debug('retina images plus page')
    freebie_plus_retina_images_tab(driver, product_files, product)
    if product.guest_author and product.guest_author_link:
        logger.debug('make guest authtor')
        plus_guest_authtor(driver, product)
    logger.debug('categories plus page')
    set_categories(driver, product)
    logger.debug('formats plus page')
    freebie_plus_formats(driver, product)
    logger.debug('metatags plus page')
    set_metatags(driver, product)
    logger.debug('plus submit')
    pr_id = plus_submit(driver, product)
    make_push(driver, pr_id, PB_LIST_PLUS_URL)


def new_prem(driver: Remote, product: schemas.UploadPrem, product_files: schemas.ProductFiles):
    logger.debug('get new prem page')
    driver.get(PB_NEW_PREM_URL)
    logger.debug('main prem page')
    prem_main_tab(driver, product, product_files, PB_NEW_PREM_URL)
    logger.debug('files prem page')
    files_tab(driver, product_files)
    logger.debug('images prem page')
    prem_images_tab(driver, product_files, product)
    logger.debug('retina prem plus page')
    prem_single_page(driver, product)
    logger.debug('categories prem page')
    set_categories(driver, product)
    logger.debug('formats prem page')
    set_prem_features(driver, product)
    set_compatibilities(driver, product)
    logger.debug('metatags prem page')
    set_metatags(driver, product)
    logger.debug('plus submit')
    pr_id = prem_submit(driver, product)
    logger.debug(f'pr_id={pr_id}')
    make_push(driver, pr_id, PB_LIST_PREM_URL)


def freebie(driver: Remote, product: schemas.UploadFreebie, product_files: schemas.ProductFiles):
    login(driver)
    new_freebie(driver, product, product_files)


def plus(driver: Remote, product: schemas.UploadPlus, product_files: schemas.ProductFiles):
    login(driver)
    new_plus(driver, product, product_files)

def prem(driver: Remote, product: schemas.UploadPrem, product_files: schemas.ProductFiles):
    login(driver)
    new_prem(driver, product, product_files)