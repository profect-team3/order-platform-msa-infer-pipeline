import os
import json
import csv
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time

# --- Configuration ---
KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = "dev.order.completed"
SAVE_PATH = "/app/data/consumed_orders.csv" # Docker 컨테이너 내부 경로

def get_kafka_consumer(broker_url, topic):
    """Kafka에 연결하고 consumer를 반환합니다."""
    while True:
        try:
            print(f"Connecting to Kafka broker at {broker_url}...")
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=broker_url,
                auto_offset_reset='earliest',
                group_id='order-consumer-group-1',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print(f"Successfully connected to Kafka and subscribed to topic '{topic}'.")
            return consumer
        except NoBrokersAvailable:
            print("Could not connect to Kafka brokers. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred while connecting to Kafka: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

def save_data_locally(data, file_path):
    """추출된 데이터를 로컬 CSV 파일에 저장합니다."""
    file_exists = os.path.isfile(file_path)
    try:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['storeId', 'totalPrice'])
            writer.writerow(data)
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    consumer = get_kafka_consumer(KAFKA_BROKER_URL, KAFKA_TOPIC)

    print("Starting to consume messages...")
    for message in consumer:
        try:
            data = message.value
            store_id = data.get('storeId')
            total_price = data.get('totalPrice')

            if store_id is not None and total_price is not None:
                print(f"Received: storeId={store_id}, totalPrice={total_price}")
                row_to_save = [store_id, total_price]
                save_data_locally(row_to_save, SAVE_PATH)
            else:
                print(f"Skipping message due to missing 'storeId' or 'totalPrice': {data}")

        except json.JSONDecodeError:
            print(f"Could not decode message value: {message.value}")
        except Exception as e:
            print(f"An error occurred while processing message: {e}")