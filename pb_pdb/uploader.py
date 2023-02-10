from pb_pdb import (browser, db_tools, graphic_tool, schemas, space_tools,
                    uploaders)


def to_pb_freebie(product: schemas.UploadFreebie):
    db_tools.set_status(product.prefix, 'Image prepare')
    product_files = space_tools.get_file_urls(product)
    product_files = graphic_tool.prepare_imgs(product, product_files)
    with browser.Browser() as chrome:
        driver = chrome.driver
        db_tools.set_status(product.prefix, 'Upload to PB')
        uploaders.pb.freebie(driver, product, product_files)
    db_tools.set_status(product.prefix, 'Uploaded to PB')
