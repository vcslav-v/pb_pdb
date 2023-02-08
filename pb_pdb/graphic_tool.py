import io

import requests
from PIL import Image

from pb_pdb import schemas, space_tools


def resize_to_x1(x2_url: str, new_name: str, prefix: str):
    resp = requests.get(x2_url)
    with io.BytesIO(resp.content) as img_file:
        img = Image.open(img_file)
        resized_img = img.resize((img.size[0]//2, img.size[1]//2))
        with io.BytesIO() as buffer:
            resized_img.convert('RGB').save(buffer, format='JPEG')
            url = space_tools.save_to_space(buffer.getvalue(), prefix, new_name)
        return url

def prepare_imgs(product: schemas.UploadProduct, product_files: schemas.ProductFiles) -> schemas.ProductFiles:
    new_product_files = product_files.copy()
    new_product_files.main_img_url = resize_to_x1(product_files.main_img_x2_url, 'main.jpg', product.prefix)
    new_product_files.thumbnail_url = resize_to_x1(product_files.thumbnail_x2_url, 'thumbnail.jpg', product.prefix)
    new_product_files.gallery_urls = []
    for i, gallery_x2_url in enumerate(product_files.gallery_x2_urls):
        new_product_files.gallery_urls.append(resize_to_x1(gallery_x2_url, f'image_for_gallery|{i+1}.jpg', product.prefix))
    return new_product_files
