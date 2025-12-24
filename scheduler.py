from pb_pdb import db_tools
from loguru import logger


if __name__ == '__main__':
    logger.info('Start set covers task')
    db_tools.set_covers()
    logger.info('Start refresh adobe counts task')
    db_tools.refresh_adobe()
    logger.info('Finished refresh adobe counts task')
