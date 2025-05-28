from pyspark.sql import SparkSession
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

def read_from_kafka():
    spark = SparkSession.builder \
        .appName("KafkaReader") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
        .getOrCreate()

    return spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .load()
