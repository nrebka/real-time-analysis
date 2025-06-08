import os
import json
import time
from kafka import KafkaConsumer
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")
KAFKA_ALERT_TOPIC = os.getenv("KAFKA_ALERT_TOPIC", "weather_alerts")

st.set_page_config(page_title="Weather Dashboard", layout="centered")
st.title("🌤 Weather Dashboard 🌤")

@st.cache_resource
def get_consumer(topic):
    return KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id=f"dashboard-{topic}",
        consumer_timeout_ms=1000,
        enable_auto_commit=True
    )

weather_consumer = get_consumer(KAFKA_TOPIC)
alert_consumer = get_consumer(KAFKA_ALERT_TOPIC)

def get_latest_message(consumer):
    consumer.poll(timeout_ms=1000)
    partitions = consumer.assignment()
    if not partitions:
        consumer.subscribe([consumer._subscription])
        consumer.poll(timeout_ms=1000)
        partitions = consumer.assignment()

    latest_data = None
    for partition in partitions:
        consumer.seek_to_end(partition)
        last_offset = consumer.position(partition)
        if last_offset == 0:
            continue
        consumer.seek(partition, last_offset - 1)
        msg = next(consumer)
        latest_data = msg.value
    return latest_data

placeholder_weather = st.empty()
placeholder_alert = st.empty()

while True:
    latest_weather = get_latest_message(weather_consumer)
    latest_alert = get_latest_message(alert_consumer)

    with placeholder_weather.container():
        st.subheader("Ostatnie dane pogodowe z Kafka:")
        if latest_weather:
            st.metric(label="Temperatura (°C)", value=f"{latest_weather['temperature']}°C")
            wind_val = latest_weather.get("windSpeed") or latest_weather.get("wind_speed") or 0
            st.metric(label="Wiatr (m/s)", value=f"{wind_val} m/s")
        else:
            st.write("Brak danych pogodowych.")

    with placeholder_alert.container():
        st.subheader("⚠️ Alert pogodowy:")
        if latest_alert and latest_alert.get("alert", False):
            details = latest_alert.get("details", {})
            for k, v in details.items():
                st.warning(v)
        else:
            st.write("Brak alertów. Temaperatura jest większa niż 5°C, wiatr jest słabszy niż 10 m/s")

    time.sleep(5)