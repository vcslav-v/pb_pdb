import dropbox
import os

DROPBOX_KEY = os.environ.get('DROPBOX_KEY', '')


def make_directory(name: str) -> str:
    new_dir_path = f'/{name}'
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        try:
            dbx.files_create_folder_v2(new_dir_path)
        except Exception:
            raise ValueError(f'folder is exist already - {name}')
    return new_dir_path


def get_share_link(path: str) -> str:
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        shared_link = dbx.sharing_create_shared_link(path)
        return shared_link.url


def rename(path: str, new_name: str) -> str:
    new_path = '/'.join(path.split('/')[:-1] + [new_name])
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        try:
            dbx.files_move_v2(path, new_path)
        except Exception:
            raise ValueError(f'folder is not exist - {new_name}')
    return new_path
