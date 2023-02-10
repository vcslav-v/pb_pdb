from pb_pdb import schemas, uploader, db_tools

def upload_product(product: schemas.UploadProduct, market: str, pr_type: str = None):
    if market == 'pb' and pr_type == 'freebie' and isinstance(product, schemas.UploadFreebie):
        db_tools.set_status(product.prefix, 'Start')
        try:
            uploader.to_pb_freebie(product)
        except Exception:
            db_tools.set_status(product.prefix, 'Error')
    db_tools.set_status(product.prefix, 'Done')
