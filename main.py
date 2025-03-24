# main.py

from kafka_reader import read_from_kafka
from data_processor import process_data
from postgres_writer import write_to_postgres

if __name__ == "__main__":
    kafka_df = read_from_kafka()
    processed_df = process_data(kafka_df)

    query = processed_df.writeStream.foreachBatch(
        lambda df, epoch_id: write_to_postgres(df, epoch_id)
    ).start()

    query.awaitTermination()
