from pb_pdb import browser, schemas, uploaders, space_tools, graphic_tool

def to_pb_freebie(product: schemas.UploadFreebie):
    product_files = space_tools.get_file_urls(product)
    product_files = graphic_tool.prepare_imgs(product, product_files)
    with browser.Browser() as chrome:
        driver = chrome.driver
        uploaders.pb.freebie(driver, product, product_files)

        

