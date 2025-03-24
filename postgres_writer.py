# postgres_writer.py

from config import POSTGRES_JDBC_URL, POSTGRES_TABLE, POSTGRES_USER, POSTGRES_PASSWORD

def write_to_postgres(df, epoch_id):
    df.write.format("jdbc") \
        .option("url", POSTGRES_JDBC_URL) \
        .option("dbtable", POSTGRES_TABLE) \
        .option("user", POSTGRES_USER) \
        .option("password", POSTGRES_PASSWORD) \
        .mode("append") \
        .save()
