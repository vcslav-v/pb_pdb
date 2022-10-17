from loguru import logger
import dropbox
import os

DROPBOX_KEY = os.environ.get('DROPBOX_KEY', '')


def dropbox_check():
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        logger.debug(dbx.file_requests_list())


if __name__ == '__main__':
    dropbox_check()
