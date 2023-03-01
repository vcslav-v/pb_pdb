import io

import requests
from PIL import Image

from pb_pdb import schemas, space_tools

PUSH_SIZE = 400


def resize_to_x1(x2_url: str, new_name: str, prefix: str):
    resp = requests.get(x2_url)
    with io.BytesIO(resp.content) as img_file:
        img = Image.open(img_file)
        img = img.resize((img.size[0]//2, img.size[1]//2))
        with io.BytesIO() as buffer:
            img.convert('RGB').save(buffer, format='JPEG')
            url = space_tools.save_to_space(buffer.getvalue(), prefix, new_name)
        return url


def create_push(img_url: str, product: schemas.UploadProduct,):
    resp = requests.get(img_url)
    with io.BytesIO(resp.content) as img_file:
        img = Image.open(img_file)
        k = min([s/PUSH_SIZE for s in img.size])
        img = img.resize([int(s / k) for s in img.size])
        x = (img.size[0] - PUSH_SIZE) // 2
        y = (img.size[1] - PUSH_SIZE) // 2
        img = img.crop((x, y, x + PUSH_SIZE, y + PUSH_SIZE))

        with io.BytesIO() as buffer:
            img.convert('RGB').save(buffer, format='JPEG')
            url = space_tools.save_to_space(buffer.getvalue(), product.prefix, f'{product.product_file_name}-by-pixelbuddha-image_for_push.jpg')
        return url


def prepare_imgs(product: schemas.UploadProduct, product_files: schemas.ProductFiles) -> schemas.ProductFiles:
    new_product_files = product_files.copy()
    new_product_files.main_img_url = resize_to_x1(product_files.main_img_x2_url, f'{product.product_file_name}-by-pixelbuddha-main.jpg', product.prefix)
    new_product_files.thumbnail_url = resize_to_x1(product_files.thumbnail_x2_url, f'{product.product_file_name}-by-pixelbuddha-thumbnail.jpg', product.prefix)
    if product_files.prem_thumbnail_x2_url:
        new_product_files.prem_thumbnail_url = resize_to_x1(product_files.prem_thumbnail_x2_url, f'{product.product_file_name}-by-pixelbuddha-prem_thumbnail.jpg', product.prefix)
    new_product_files.gallery_urls = []
    for i, gallery_x2_url in enumerate(product_files.gallery_x2_urls):
        new_product_files.gallery_urls.append(resize_to_x1(gallery_x2_url, f'{product.product_file_name}-by-pixelbuddha-image_for_gallery|{i+1}.jpg', product.prefix))
    if not product_files.push_url:
        new_product_files.push_url = create_push(new_product_files.thumbnail_x2_url, product)
    return new_product_files
