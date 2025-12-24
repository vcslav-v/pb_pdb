from pb_pdb import uploader, db_tools
from datetime import datetime


if __name__ == '__main__':
    db_tools.set_covers()
    db_tools.refresh_adobe()
