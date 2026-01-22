"""Constants for XBloom MQTT integration."""

DOMAIN = "xbloom_mqtt"

# MQTT Topics
MQTT_BASE_TOPIC = "xbloom/xbloom"
MQTT_COMMAND_TOPIC = f"{MQTT_BASE_TOPIC}/command"
MQTT_STATUS_TOPIC = f"{MQTT_BASE_TOPIC}/status"

# Default values
DEFAULT_VOLUME = 100
DEFAULT_TEMPERATURE = 93
DEFAULT_GRIND_SIZE = 50
DEFAULT_RPM = 80
DEFAULT_FLOW_RATE = 3.0

# Config keys
CONF_RECIPES = "recipes"
