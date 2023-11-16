from pb_pdb import db_tools, pb_tools
from loguru import logger


if __name__ == '__main__':
    logger.info('Start bulk tag task')
    bulk_tag_task = db_tools.get_bulk_tag_task()
    if bulk_tag_task:
        logger.info(f'Found bulk tag task: {bulk_tag_task}')
        try:
            pb_tools.bulk_add_tag(bulk_tag_task)
        except Exception as e:
            logger.error('Error in bulk tag task')
            logger.error(e)
            db_tools.deactivate_bulk_tag_task(bulk_tag_task.db_id)
            raise e
