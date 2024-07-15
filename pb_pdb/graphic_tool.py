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

