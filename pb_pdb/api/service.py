from pb_pdb import schemas, uploader, db_tools


def upload_product(product: schemas.UploadProduct, market: str, pr_type: str = None):
    if market == 'pb':
        db_tools.set_status(product.prefix, 'Start')
        try:
            uploader.to_pb(product)
        except Exception:
            db_tools.set_status(product.prefix, 'Error')
        else:
            db_tools.set_status(product.prefix, 'Done')
