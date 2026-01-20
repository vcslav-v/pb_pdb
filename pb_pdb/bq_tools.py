from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import date, timedelta
import io
from pb_pdb import db_tools, config
    

def sync():
    bq_client = bigquery.Client()
    for table_name, df in db_tools.get_all_products_data():
        table_id = f'{config.BQ_PROJECT}.{config.BQ_DATASET}.{table_name}'
        job_config = bigquery.LoadJobConfig(
            write_disposition='WRITE_TRUNCATE',
            source_format=bigquery.SourceFormat.PARQUET,
        )
        bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
