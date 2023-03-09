from pb_pdb import uploader, db_tools
from datetime import datetime


if __name__ == '__main__':
    product_schedule = db_tools.get_product_schedule(datetime.utcnow())
    for product in product_schedule:
        uploader.make_live(product.edit_url)