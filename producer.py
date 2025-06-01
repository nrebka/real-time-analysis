
import requests
import json
import time
from kafka import KafkaProducer

KAFKA_BROKER = 'broker:9092'
TOPIC_NAME = 'weather-poland'

# Lista lokalizacji (województwa)
LOCATIONS = [
    ("dolnośląskie", 51.1079, 17.0385),
    ("kujawsko-pomorskie", 53.1235, 18.0084),
    ("lubelskie", 51.2465, 22.5684),
    ("lubuskie", 52.7368, 15.2288),
    ("łódzkie", 51.7592, 19.4550),
    ("małopolskie", 50.0647, 19.9450),
    ("mazowieckie", 52.2297, 21.0122),
    ("opolskie", 50.6751, 17.9213),
    ("podkarpackie", 50.0413, 22.0059),
    ("podlaskie", 53.1325, 23.1688),
    ("pomorskie", 54.3520, 18.6466),
    ("śląskie", 50.2649, 19.0238),
    ("świętokrzyskie", 50.8661, 20.6286),
    ("warmińsko-mazurskie", 53.7784, 20.4801),
    ("wielkopolskie", 52.4064, 16.9252),
    ("zachodniopomorskie", 53.4285, 14.5528),
]

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

try:
    while True:
        for name, lat, lon in LOCATIONS:
            data = get_weather(lat, lon)
            if data and "current_weather" in data:
                current = data["current_weather"]
                payload = {
                    "region": name,
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": current["time"],
                    "temperature": current["temperature"],
                    "wind_speed": current["windspeed"],
                    "wind_direction": current["winddirection"],
                    "weather_code": current["weathercode"]
                }
                producer.send(TOPIC_NAME, payload)
                print(f"[{name}] -> {payload['temperature']}°C, wind {payload['wind_speed']} km/h")
        time.sleep(900)  # 15 minut
except KeyboardInterrupt:
    print("Zatrzymano producenta.")
