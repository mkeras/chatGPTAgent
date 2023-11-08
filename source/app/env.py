from os import environ
from random import randint

__true = ['True', 'true', '1']

DEBUG = environ.get('DEBUG', default=False) in ['True', 'true', '1']
INCLUDE_ORIGINAL_DATA = environ.get('INCLUDE_ORIGINAL_DATA', default='True') in __true

OPENAI_API_KEY = environ.get('OPENAI_API_KEY')

GPT_MODEL = environ.get('GPT_MODEL', default='gpt-4-1106-preview')

GPT_SYSTEM_PROMPT = environ.get('GPT_SYSTEM_PROMPT')
GPT_USER_PROMPT = environ.get('GPT_USER_PROMPT', default = '')

MQTT_SUBSCRIBE_TOPIC = environ.get('MQTT_SUBSCRIBE_TOPIC')
MQTT_PUBLISH_TOPIC = environ.get('MQTT_PUBLISH_TOPIC')

MQTT_HOST = environ.get('MQTT_HOST')
MQTT_PORT = int(environ.get('MQTT_PORT', default=8883))
MQTT_USERNAME = environ.get('MQTT_USERNAME')
MQTT_PASSWORD = environ.get('MQTT_PASSWORD')

MQTT_CLIENT_ID = environ.get('MQTT_CLIENT_ID', default=f'chatGPT_agent_{randint(100000, 999999)}')

MQTT_USE_TLS = environ.get('MQTT_USE_TLS', default='True') in __true


AGENT_NAME = environ.get('AGENT_NAME', default=MQTT_CLIENT_ID)