from pyspark.sql.functions import *
from pyspark.sql.types import *

# --- 1. CONFIGURATION ---
# Use the schema created in the previous step: 'workspace.data_staging'
CATALOG_NAME = "workspace"
SCHEMA_NAME = "data_staging"
FULL_SCHEMA_PATH = f"{CATALOG_NAME}.{SCHEMA_NAME}"

# Kinesis Stream Details
kinesis_stream_name = "iot-sensor-data-stream"
aws_region = "us-east-1"

# CRITICAL: S3 Base Path for CHECKPOINTS ONLY
# Checkpoints must be outside the managed schema path for safety, but still within your bucket.
# substitute 'yourbucketname' with your actual bucket name
S3_CHECKPOINT_BASE_PATH = "s3://yourbucketnamehere/checkpoints/iot_stream/"

RAW_CHECKPOINT_PATH = S3_CHECKPOINT_BASE_PATH + "raw_stream/"
PROCESSED_CHECKPOINT_PATH = S3_CHECKPOINT_BASE_PATH + "processed_stream/"

# Final table names (Unity Catalog managed tables)
RAW_TABLE_NAME = f"{FULL_SCHEMA_PATH}.iot_sensor_raw"
PROCESSED_TABLE_NAME = f"{FULL_SCHEMA_PATH}.iot_sensor_processed"

print(f"Tables will be created in: {FULL_SCHEMA_PATH}")
print(f"Raw Table: {RAW_TABLE_NAME}")
print(f"Processed Table: {PROCESSED_TABLE_NAME}")
# ---------------------

# Set the current catalog and schema for the session
spark.sql(f"USE CATALOG {CATALOG_NAME}")
spark.sql(f"USE SCHEMA {SCHEMA_NAME}")

# 2. Define the Schema for the expected JSON events
data_schema = StructType([
    StructField("device_id", StringType()),
    StructField("timestamp", LongType()), # Use LongType for epoch time
    StructField("metrics", StructType([
        StructField("temperature_c", FloatType()),
        StructField("pressure_hpa", FloatType()),
        StructField("humidity_percent", FloatType())
    ])),
    StructField("status", StringType()),
    StructField("region", StringType())
])

# 3. Read the Kinesis Stream
print("\nReading Kinesis Stream...")
kinesis_raw_df = spark.readStream \
    .format("kinesis") \
    .option("streamName", kinesis_stream_name) \
    .option("region", aws_region) \
    .option("initialPosition", "latest") \
    .load()

# 4. Process and Transform the Data

# Extract and cast the binary Kinesis 'data' payload to string
json_data_df = kinesis_raw_df \
    .select(
        col("data").cast("string").alias("json_payload"),
        col("approximateArrivalTimestamp").alias("kinesis_time")
    )

# Apply schema to parse the structured data and add derived columns
processed_df = json_data_df \
    .withColumn(
        "parsed_data", from_json(col("json_payload"), data_schema)
    ) \
    .select(
        col("parsed_data.*"),
        col("kinesis_time")
    ) \
    .withColumn(
        "event_timestamp", (col("timestamp") / 1000).cast(TimestampType()) # Convert epoch milliseconds to Timestamp
    ) \
    .withColumn(
        "temperature_c", col("metrics.temperature_c")
    ) \
    .withColumn(
        "is_critical", when(col("temperature_c") > 28.0, True).otherwise(False)
    ) \
    .drop("metrics") # Drop the complex 'metrics' struct column

# 5. Start Streams and Write to Unity Catalog (Raw and Processed)
# NOTE: Using .toTable() creates a MANAGED Delta table inside the data_staging schema.

# A. RAW Data Write
# Writes the raw JSON data to the managed table: workspace.data_staging.iot_sensor_raw
print(f"\nStarting RAW data stream to Unity Catalog table: {RAW_TABLE_NAME}")

raw_query = (json_data_df.writeStream
    .format("delta")
    .option("checkpointLocation", RAW_CHECKPOINT_PATH)
    .outputMode("append")
    .trigger(processingTime='10 seconds')
    .toTable(RAW_TABLE_NAME) 
)


# B. PROCESSED Data Write
# Writes the cleaned, structured data to the managed table: workspace.data_staging.iot_sensor_processed
print(f"\nStarting PROCESSED data stream to Unity Catalog table: {PROCESSED_TABLE_NAME}")

processed_query = (processed_df.writeStream
    .format("delta")
    .option("checkpointLocation", PROCESSED_CHECKPOINT_PATH)
    .outputMode("append")
    .trigger(processingTime='10 seconds')
    .toTable(PROCESSED_TABLE_NAME) 
)


print("\n--- SUCCESS: Both Raw and Processed Streams Started. ---")
print("ACTION REQUIRED: start your IoT Simulator to begin data ingestion.")