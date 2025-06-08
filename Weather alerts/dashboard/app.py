import os
import json
from kafka import KafkaConsumer
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")

st.set_page_config(page_title="Weather Dashboard", layout="centered")
st.title("🌤 Weather Dashboard - Real-time Kafka Stream")

@st.cache_resource
def get_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="weather-dashboard",
        enable_auto_commit=True,
        consumer_timeout_ms=1000
    )

consumer = get_consumer()

st.write("📡 Ostatnie dane pogodowe z Kafka:")

def get_latest_message(consumer):
    consumer.poll(timeout_ms=1000)  # krótki poll, żeby wymusić fetch
    partitions = consumer.assignment()
    if not partitions:
        consumer.subscribe([KAFKA_TOPIC])
        consumer.poll(timeout_ms=1000)
        partitions = consumer.assignment()

    latest_data = None
    for partition in partitions:
        consumer.seek_to_end(partition)
        last_offset = consumer.position(partition)
        if last_offset == 0:
            continue  # brak wiadomości w tym partycji
        consumer.seek(partition, last_offset - 1)
        msg = next(consumer)
        latest_data = msg.value
    return latest_data

latest_data = get_latest_message(consumer)

if latest_data:
    st.metric(label="🌡 Temperatura (°C)", value=f"{latest_data['temperature']}°C")
    st.metric(label="💨 Wiatr (m/s)", value=f"{latest_data['wind_speed']} m/s")
else:
    st.write("Brak danych do wyświetlenia.")