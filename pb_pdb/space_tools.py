from pb_pdb import schemas, do_app
from boto3 import session as s3_session
from urllib.parse import urlparse



def get_save_s3_obj(s3_objs: list[dict], filename: str, prefix, required=True, multitude=False):
    if multitude:
        result = list(filter(
            lambda x: x['Key'].split('.')[0].startswith(f'temp/{prefix}/{filename}|'), s3_objs)
        )
        result.sort(key=lambda x: int(x['Key'].split('.')[0].split('|')[-1]))
    else:
        result = list(filter(
            lambda x: x['Key'].split('.')[0] == f'temp/{prefix}/{filename}', s3_objs)
        )
    if not result and not required:
        return result
    elif not result and required:
        #TODO make exeption
        raise Exception
    if multitude and result:
        return list(map(lambda x: x['Key'], result))
    elif multitude and not result:
        return []
    return result[0]['Key']


def get_s3_link(client, key):
    return client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': do_app.DO_SPACE_BUCKET,
            'Key': key,
        },
        ExpiresIn=3000
    )


def get_file_urls(product) -> schemas.ProductFiles:
    do_session = s3_session.Session()
    client = do_session.client(
        's3',
        region_name=do_app.DO_SPACE_REGION,
        endpoint_url=do_app.DO_SPACE_ENDPOINT,
        aws_access_key_id=do_app.DO_SPACE_KEY,
        aws_secret_access_key=do_app.DO_SPACE_SECRET
    )
    s3_objs = client.list_objects(Bucket=do_app.DO_SPACE_BUCKET)['Contents']
    img_for_push = get_save_s3_obj(s3_objs, f'{product.product_file_name}-by-pixelbuddha-image_for_push', product.prefix, required=False)
    gallery = get_save_s3_obj(s3_objs, f'{product.product_file_name}-by-pixelbuddha-image_for_gallery_x2', product.prefix, required=False, multitude=True)
    main_img = get_save_s3_obj(s3_objs, f'{product.product_file_name}-by-pixelbuddha-main_x2', product.prefix)
    thumbnail_img = get_save_s3_obj(s3_objs, f'{product.product_file_name}-by-pixelbuddha-thumbnail_x2', product.prefix)
    product_file = get_save_s3_obj(s3_objs, product.product_file_name, product.prefix)

    result = schemas.ProductFiles(
        product_url=get_s3_link(client, product_file),
        main_img_x2_url=get_s3_link(client, main_img),
        gallery_x2_urls=[get_s3_link(client, gallery_img) for gallery_img in gallery],
        thumbnail_x2_url=get_s3_link(client, thumbnail_img),
    )
    if img_for_push:
        result.push_url = get_s3_link(client, img_for_push)

    client.close()
    return result


def save_to_space(data: str, prefix: str, new_name: str):
    do_session = s3_session.Session()
    client = do_session.client(
        's3',
        region_name=do_app.DO_SPACE_REGION,
        endpoint_url=do_app.DO_SPACE_ENDPOINT,
        aws_access_key_id=do_app.DO_SPACE_KEY,
        aws_secret_access_key=do_app.DO_SPACE_SECRET
    )
    key = f'temp/{prefix}/{new_name}'
    client.put_object(
        Bucket=do_app.DO_SPACE_BUCKET,
        Body=data,
        Key=key,
        ACL='public-read',
        StorageClass='REDUCED_REDUNDANCY',
        ContentType='application/octet-stream',
    )
    return get_s3_link(client, key)


def get_filename_from_url(url: str):
    return urlparse(url).path.split('/')[-1]
