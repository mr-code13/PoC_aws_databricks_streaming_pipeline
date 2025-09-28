import boto3
import json

STREAM_NAME = "iot-sensor-data-stream"
REGION = "us-east-1" 

client = boto3.client("kinesis", region_name=REGION)

# shard iterator
shard_it = client.get_shard_iterator(
    StreamName=STREAM_NAME,
    ShardId="shardId-000000000000",
    ShardIteratorType="TRIM_HORIZON"  
)["ShardIterator"]

print(f"Reading records from stream: {STREAM_NAME} ...")

while True:
    response = client.get_records(ShardIterator=shard_it, Limit=10)
    for record in response["Records"]:
        data = json.loads(record["Data"].decode("utf-8"))
        print(data)
    
    # Advance the shard iterator
    shard_it = response["NextShardIterator"]
