import clickhouse_connect
from config.db_config import CLICKHOUSE_SETTINGS

def get_clickhouse_client():
    return clickhouse_connect.get_client(**CLICKHOUSE_SETTINGS)