from loguru import logger
import dropbox
import os

DROPBOX_KEY = os.environ.get('DROPBOX_KEY', '')
APP_KEY = os.environ.get('APP_KEY', '')


def dropbox_check():
    with dropbox.Dropbox(oauth2_refresh_token=DROPBOX_KEY, app_key=APP_KEY) as dbx:
        logger.debug(dbx.file_requests_list())


if __name__ == '__main__':
    dropbox_check()
