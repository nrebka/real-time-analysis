import os
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv

load_dotenv()

# Logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")
KAFKA_ALERT_TOPIC = os.getenv("KAFKA_ALERT_TOPIC", "weather_alerts")

ALERT_TEMP = float(os.getenv("ALERT_TEMP", 10))
ALERT_WIND = float(os.getenv("ALERT_WIND", 1))

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="weather-alerts",
    enable_auto_commit=True
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

logging.info("⏳ Oczekiwanie na dane pogodowe do analizy alertów...")

for message in consumer:
    try:
        weather = message.value
        temp = weather.get("temperature")
        wind = weather.get("windSpeed") or weather.get("wind_speed")  

        logging.info(f"🌡 Temp: {temp}, 💨 Wiatr: {wind}")

        alert_triggered = False
        alert_info = {}

        if temp is None or wind is None:
            logging.warning("⚠️ Brak wymaganych danych (temperature/windSpeed) w wiadomości")
            continue

        if temp < ALERT_TEMP:
            alert_triggered = True
            alert_info["temperature_alert"] = f"Temperatura niska: {temp}°C < {ALERT_TEMP}°C"

        if wind > ALERT_WIND:
            alert_triggered = True
            alert_info["wind_alert"] = f"Wiatr silny: {wind} m/s > {ALERT_WIND} m/s"

        if alert_triggered:
            alert_message = {
                "alert": True,
                "details": alert_info,
                "original_data": weather
            }
            producer.send(KAFKA_ALERT_TOPIC, alert_message)
            logging.warning(f"⚠️ Wysłano alert do Kafka: {alert_message}")

    except Exception as e:
        logging.error(f"❌ Błąd w konsumerze alertów: {e}")