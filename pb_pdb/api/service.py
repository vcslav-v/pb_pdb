from pb_pdb import schemas, uploader, db_tools


def upload_product(product: schemas.UploadProduct, market: str, pr_type: str = None):
    if market == 'pb' and pr_type == 'freebie' and isinstance(product, schemas.UploadFreebie):
        db_tools.set_status(product.prefix, 'Start')
        try:
            uploader.to_pb_freebie(product)
        except Exception:
            db_tools.set_status(product.prefix, 'PB_Error')

    if market == 'pb' and pr_type == 'plus' and isinstance(product, schemas.UploadPlus):
        db_tools.set_status(product.prefix, 'Start')
        try:
            uploader.to_pb_plus(product)
        except Exception:
            db_tools.set_status(product.prefix, 'PB_Error')

    if market == 'pb' and pr_type == 'prem' and isinstance(product, schemas.UploadPrem):
        db_tools.set_status(product.prefix, 'Start')
        try:
            uploader.to_pb_prem(product)
        except Exception:
            db_tools.set_status(product.prefix, 'PB_Error')
    db_tools.set_status(product.prefix, 'Done')
