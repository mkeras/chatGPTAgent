from os import environ
from random import randint

__true = ['True', 'true', '1']

"""
Environment vars used by sparkplug-node
"""
DEBUG = environ.get('DEBUG', default=False) in __true

MQTT_HOST = environ.get('MQTT_HOST')
MQTT_PORT = int(environ.get('MQTT_PORT', default=8883))
MQTT_USERNAME = environ.get('MQTT_USERNAME')
MQTT_PASSWORD = environ.get('MQTT_PASSWORD')

MQTT_CLIENT_ID = environ.get('MQTT_CLIENT_ID', default=f'chat-gpt-agent-{randint(100000, 999999)}')

MQTT_USE_TLS = environ.get('MQTT_USE_TLS', default='True') in __true


SPARKPLUG_GROUP_ID = environ.get('SPARKPLUG_GROUP_ID')
SPARKPLUG_EDGE_NODE_ID = environ.get('SPARKPLUG_EDGE_NODE_ID', default=MQTT_CLIENT_ID)


DATA_DIRECTORY = environ.get('DATA_DIRECTORY', default=f'/etc/sparkplug/{SPARKPLUG_GROUP_ID}/{SPARKPLUG_EDGE_NODE_ID}/').replace(' ', '_')

CONFIG_FILEPATH = environ.get('CONFIG_FILEPATH', default=f'{DATA_DIRECTORY}config.json')

MEMORY_TAGS_FILEPATH = environ.get('MEMORY_TAGS_FILEPATH', default=f'{DATA_DIRECTORY}memory-tags.json')

"""
Environment vars used by gpt-agent
"""

OPENAI_API_KEY = environ.get('OPENAI_API_KEY')

MQTT_SUBSCRIBE_TOPIC = environ.get('MQTT_SUBSCRIBE_TOPIC')
MQTT_PUBLISH_TOPIC = environ.get('MQTT_PUBLISH_TOPIC')

GPT_MODEL = environ.get('GPT_MODEL')

GPT_SYSTEM_PROMPT = environ.get('GPT_SYSTEM_PROMPT')
GPT_USER_PROMPT = environ.get('GPT_USER_PROMPT')

'''

INCLUDE_ORIGINAL_DATA = environ.get('INCLUDE_ORIGINAL_DATA', default='True') in __true









MQTT_HOST = environ.get('MQTT_HOST')
MQTT_PORT = int(environ.get('MQTT_PORT', default=8883))
MQTT_USERNAME = environ.get('MQTT_USERNAME')
MQTT_PASSWORD = environ.get('MQTT_PASSWORD')

MQTT_CLIENT_ID = environ.get('MQTT_CLIENT_ID', default=f'chatGPT_agent_{randint(100000, 999999)}')

MQTT_USE_TLS = environ.get('MQTT_USE_TLS', default='True') in __true

AGENT_NAME = environ.get('AGENT_NAME', default=MQTT_CLIENT_ID)


SPARKPLUG_GROUP_ID = environ.get('SPARKPLUG_GROUP_ID', default='chatGPT Transform')
SPARKPLUG_EDGE_NODE_ID = environ.get('SPARKPLUG_EDGE_NODE_ID', default=AGENT_NAME)

DATA_DIRECTORY = environ.get('DATA_DIRECTORY', default=f'/etc/sparkplug/{SPARKPLUG_GROUP_ID}/{SPARKPLUG_EDGE_NODE_ID}/').replace(' ', '_')
'''