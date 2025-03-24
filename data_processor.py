# data_processor.py

from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

def process_data(df):
    schema = StructType([
        StructField("Date", StringType(), True),
        StructField("Open", DoubleType(), True),
        StructField("High", DoubleType(), True),
        StructField("Low", DoubleType(), True),
        StructField("Close", DoubleType(), True),
        StructField("Volume", StringType(), True)
    ])
    
    return df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
