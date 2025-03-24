# kafka_reader.py

from pyspark.sql import SparkSession
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

def read_from_kafka():
    spark = SparkSession.builder.appName("KafkaReader").getOrCreate()
    return spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .load()
