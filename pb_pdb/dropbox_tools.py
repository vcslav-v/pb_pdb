import dropbox
import os

DROPBOX_KEY = os.environ.get('DROPBOX_KEY', '')


def make_directory(category: str, title: str, full_name: str) -> str:
    new_dir_path = f'/Products/{category}/{full_name}'
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        try:
            dbx.files_create_folder_v2(new_dir_path)
        except Exception:
            raise ValueError(f'folder is exist already - {full_name}')
        
        dbx.files_create_folder_v2(new_dir_path + f'/{title}')
        dbx.files_create_folder_v2(new_dir_path + '/Preview files')
        dbx.files_create_folder_v2(new_dir_path + '/Preview source')
        dbx.files_create_folder_v2(new_dir_path + '/Source images')

    return new_dir_path


def get_share_link(path: str) -> str:
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        shared_link = dbx.sharing_create_shared_link(path)
        return shared_link.url


def rename(path: str, new_name: str, title: str, old_title: str) -> str:
    new_path = '/'.join(path.split('/')[:-1] + [new_name])
    with dropbox.Dropbox(DROPBOX_KEY) as dbx:
        try:
            dbx.files_move_v2(path, new_path)
        except Exception:
            raise ValueError(f'folder is not exist - {new_name}')
        
        dbx.files_move_v2(path + f'/{old_title}', new_path + f'/{title}')
    return new_path
