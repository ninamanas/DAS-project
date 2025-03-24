import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType, LongType

# Load schema from JSON file
with open("schema.json", "r") as schema_file:
    schema_json = json.load(schema_file)

# Create SparkSession
spark = SparkSession.builder \
    .appName("StockStreamProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC_NAME = 'stock_data'

# PostgreSQL Settings
DB_HOST = "localhost"
DB_NAME = "stock_data"
DB_USER = "postgres"
DB_PASSWORD = "your_password"  # Replace with your PostgreSQL password

# Define Schema for JSON Data (convert JSON to Spark schema)
schema = StructType([
    StructField("Date", StringType(), True),
    StructField("Open", DoubleType(), True),
    StructField("High", DoubleType(), True),
    StructField("Low", DoubleType(), True),
    StructField("Close", DoubleType(), True),
    StructField("Adj Close", DoubleType(), True),
    StructField("Volume", LongType(), True),
    StructField("symbol", StringType(), True)
])

# Read Data from Kafka Topic
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", TOPIC_NAME) \
    .load()

# [Previous imports and setup remain the same until processed_df...]

# Process Data in Real-Time
processed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# ===== ADD THIS RIGHT AFTER PROCESSED_DF CREATION =====
# Rename columns to match PostgreSQL table
processed_df = processed_df.withColumnRenamed("Date", "date") \
                          .withColumnRenamed("Open", "open") \
                          .withColumnRenamed("High", "high") \
                          .withColumnRenamed("Low", "low") \
                          .withColumnRenamed("Close", "close") \
                          .withColumnRenamed("Adj Close", "adj_close") \
                          .withColumnRenamed("Volume", "volume") \
                          .withColumnRenamed("symbol", "symbol")  # Keep symbol as is

# Debug output
print("========= PROCESSED DATA SCHEMA =========")
processed_df.printSchema()

print("========= SAMPLE DATA =========")
processed_df.show(5, truncate=False)

# ===== MODIFY YOUR write_to_postgres FUNCTION =====
def write_to_postgres(df, epoch_id):
    # Debug before writing
    print(f"========= BATCH {epoch_id} - WRITING TO POSTGRES =========")
    df.show(5, truncate=False)
    
    df.write \
        .format("jdbc") \
        .option("url", f"jdbc:postgresql://{DB_HOST}:5432/{DB_NAME}") \
        .option("dbtable", "stock_prices") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .mode("append") \
        .save()

