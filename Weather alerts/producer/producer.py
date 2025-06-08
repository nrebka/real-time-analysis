import json
import time
import requests
import os
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TOMORROW_API_KEY")
LATITUDE = os.getenv("LATITUDE", "52.2297")
LONGITUDE = os.getenv("LONGITUDE", "21.0122")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def fetch_weather():
    url = f"https://api.tomorrow.io/v4/timelines?location={LATITUDE},{LONGITUDE}&fields=temperature,windSpeed&timesteps=current&units=metric&apikey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        values = data['data']['timelines'][0]['intervals'][0]['values']
        print(f"Pobrano dane pogodowe: {values}")
        return values
    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych pogodowych: {e}")
        return None

while True:
    weather_data = fetch_weather()
    if weather_data:
        producer.send(KAFKA_TOPIC, weather_data)
        print(f"✅ Wysłano dane do Kafka: {weather_data}")
    time.sleep(POLL_INTERVAL)