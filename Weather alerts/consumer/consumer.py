import os
import json
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

print("[consumer] Consumer started")


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")

consumer = KafkaConsumer(
    KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="weather-dashboard",
        enable_auto_commit=True,
        session_timeout_ms=30000,     # 30 sekund
        heartbeat_interval_ms=10000
)

print("[consumer] Waiting for messages...")
for message in consumer:
    weather = message.value
    print(f"[consumer] Received weather data: {weather}")