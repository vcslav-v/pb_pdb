from pb_pdb import db_tools, pb_tools


if __name__ == '__main__':
    bulk_tag_task = db_tools.get_bulk_tag_task()
    if bulk_tag_task:
        pb_tools.bulk_add_tag(bulk_tag_task)
