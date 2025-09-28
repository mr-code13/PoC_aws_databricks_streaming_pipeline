import boto3
import json
import time
import random
import uuid

# destination stream for the messages
KINESIS_STREAM_NAME = "iot-sensor-data-stream" 

# Initializing the Kinesis client
try:
    kinesis_client = boto3.client('kinesis')
    print(f"Boto3 Kinesis client initialized successfully for stream: {KINESIS_STREAM_NAME}")
except Exception as e:
    print(f"Error initializing Boto3 client: {e}")
    exit()

def generate_iot_reading(device_id):
    """Generates a simulated IoT sensor reading payload."""
    timestamp = int(time.time() * 1000) # Milliseconds since epoch
    
    # Generating random, realistic-ish sensor data
    temperature = round(random.uniform(18.0, 30.0), 2)
    pressure = round(random.uniform(980.0, 1030.0), 2)
    humidity = round(random.uniform(40.0, 70.0), 2)
    
    # Simulating device status
    status = random.choice(["HEALTHY", "WARNING", "CRITICAL"])
    
    # Create the payload dictionary
    payload = {
        "device_id": device_id,
        "timestamp": timestamp,
        "metrics": {
            "temperature_c": temperature,
            "pressure_hpa": pressure,
            "humidity_percent": humidity
        },
        "status": status,
        "region": "us-east-1" # Assuming your CDK deployment is in a region that supports Databricks Free Tier
    }
    
    return payload

def send_to_kinesis(data, client):
    """Sends the data payload to the Kinesis Stream."""
    
    # Kinesis requires the data to be bytes (serialized JSON) and a PartitionKey
    partition_key = data['device_id']
    data_bytes = json.dumps(data).encode('utf-8')
    
    try:
        response = client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=data_bytes,
            PartitionKey=partition_key
        )
        # Printing success message
        print(f"Sent record to shard: {response['ShardId']} | Sequence: {response['SequenceNumber']}")
    except Exception as e:
        print(f"FATAL ERROR sending record to Kinesis: {e}")
        time.sleep(5) # Wait before retrying on error

def main_simulation_loop():
    """Main loop to simulate multiple IoT devices streaming data."""
    
    # Simulating a small fleet of devices
    device_ids = [str(uuid.uuid4()) for _ in range(5)]
    
    print("--- Starting IoT Sensor Data Simulation ---")
    print(f"Streaming data to Kinesis Stream: {KINESIS_STREAM_NAME}")
    print("Press Ctrl+C to stop the stream.")
    
    try:
        while True:
            for device_id in device_ids:
                reading = generate_iot_reading(device_id)
                send_to_kinesis(reading, kinesis_client)
            
            # Sending 5 records (one from each device) every second
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\n--- Simulation stopped by user (Ctrl+C) ---")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main_simulation_loop()
