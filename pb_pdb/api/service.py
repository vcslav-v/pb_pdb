from pb_pdb import schemas, uploader

def upload_product(product: schemas.UploadProduct, market: str, pr_type: str = None):
    if market == 'pb' and pr_type == 'freebie' and isinstance(product, schemas.UploadFreebie):
        uploader.to_pb_freebie(product)
