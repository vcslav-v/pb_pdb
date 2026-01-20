import os
import sys
from dotenv import load_dotenv
from loguru import logger

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')
    IS_DEV = True
    load_dotenv(dotenv_path)
    logger.info('Loaded .env file')
else:
    logger.remove()
    logger.add(sys.stderr, level='INFO')
    IS_DEV = False

#BigQuery
AUTH_FILE_PATH = os.environ.get('AUTH_FILE_PATH', '')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = AUTH_FILE_PATH

if AUTH_FILE_PATH and not IS_DEV:
    try:
        with open(AUTH_FILE_PATH, 'w') as f:
            f.write(
                os.environ.get(
                    'AUTH_FILE_DATA',
                    ''''''
                )
            )
    except Exception as e:
        logger.error(f"Failed to write to AUTH_FILE_PATH: {e}")
else:
    logger.warning("AUTH_FILE_PATH is not set or invalid. Skipping file write.")

# bigquery
BQ_PROJECT = os.environ.get('BQ_PROJECT', '')
BQ_DATASET = os.environ.get('BQ_DATASET', '')

IMG_PRODUCT_IMG_TEMPLATE = os.environ.get('IMG_PRODUCT_IMG_TEMPLATE', '')