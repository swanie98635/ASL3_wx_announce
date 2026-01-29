from env_canada import ECData
import json

lat = 44.0
lon = -73.0 # Using my test coords from config.yaml.example or config.yaml?
# config.yaml has 45.4215, -75.6972 for Ottawa.
# Wait, my config_fixed.yaml had:
#     lat: 45.4215
#     lon: -75.6972

# I will test with those.
try:
    ec = ECData(coordinates=(45.4215, -75.6972))
    ec.update()
    print(f"Type of metadata: {type(ec.metadata)}")
    print(f"Metadata content: {ec.metadata}")
except Exception as e:
    print(f"Error: {e}")
