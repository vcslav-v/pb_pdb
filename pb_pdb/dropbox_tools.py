import dropbox
import os

DROPBOX_KEY = os.environ.get('DROPBOX_KEY', '')
APP_KEY = os.environ.get('APP_KEY', '')
BRUSH_APES_CATEGORY = os.environ.get('BRUSH_APES_CATEGORY', 'BRUSH APES')


def make_directory(category: str, title: str, full_name: str) -> str:
    new_dir_path = f'/Products/{category}/{full_name}'
    with dropbox.Dropbox(oauth2_refresh_token=DROPBOX_KEY, app_key=APP_KEY) as dbx:
        try:
            dbx.files_create_folder_v2(new_dir_path)
        except Exception:
            raise ValueError(f'folder is exist already - {full_name}')

        is_brush_apes = category == BRUSH_APES_CATEGORY

        dbx.files_create_folder_v2(new_dir_path + f'/{title}')
        dbx.files_create_folder_v2(new_dir_path + '/Preview files')
        dbx.files_create_folder_v2(new_dir_path + '/Preview source')
        dbx.files_create_folder_v2(new_dir_path + '/Source images')
        if is_brush_apes:
            dbx.files_create_folder_v2(new_dir_path + '/Videos')
        else:
            dbx.files_create_folder_v2(new_dir_path + '/Freepik')
            dbx.files_create_folder_v2(new_dir_path + '/Adobe')

    return new_dir_path


def get_share_link(path: str) -> str:
    with dropbox.Dropbox(oauth2_refresh_token=DROPBOX_KEY, app_key=APP_KEY) as dbx:
        shared_link = dbx.sharing_create_shared_link(path)
        return shared_link.url


def get_cover_file_content(path: str) -> str:
    with dropbox.Dropbox(oauth2_refresh_token=DROPBOX_KEY, app_key=APP_KEY) as dbx:
        preview_dir = f'{path}/Preview files'
        files_list = dbx.files_list_folder(preview_dir)
        files_list = [file._name_value for file in files_list.entries]
        files_list.sort()
        preview_file_name = ''
        for file_name in files_list:
            if file_name.endswith(('.jpg', '.png', '.jpeg')):
                preview_file_name = file_name
                break
        else:
            raise ValueError(f'cover is not exist - {path}')
        preview_path = f'{preview_dir}/{preview_file_name}'
        _metadata, res = dbx.files_download(preview_path)
        return res.content


def rename(path: str, new_name: str, title: str, old_title: str) -> str:
    new_path = '/'.join(path.split('/')[:-1] + [new_name])
    if path == new_path:
        return new_path
    with dropbox.Dropbox(oauth2_refresh_token=DROPBOX_KEY, app_key=APP_KEY) as dbx:
        try:
            dbx.files_move_v2(path, new_path)
        except Exception:
            raise ValueError(f'folder is not exist - {new_name}')

        old_publish_dir = new_path + f'/{old_title}'
        new_publish_dir = new_path + f'/{title}'
        dbx.files_move_v2(old_publish_dir, new_publish_dir)
    return new_path
