from . import env

import openai
import json
import paho.mqtt.client as mqtt
import time
import uuid

openai.api_key = env.OPENAI_API_KEY

SYSTEM_PROMPT = {'role': 'system', 'content': env.GPT_SYSTEM_PROMPT}

def millis() -> int:
    return int(time.time() * 1000)

config = {
    'chat-gpt-model': env.GPT_MODEL,
    'system-prompt': env.GPT_SYSTEM_PROMPT,
    'user-prompt': env.GPT_USER_PROMPT if env.GPT_USER_PROMPT else None
}


DEBUG = env.DEBUG

log_topic = 'gpt-transform-v1/logging/dev'

root_topic = f'gpt-transform-v1/{env.AGENT_NAME}/'


def on_incoming_data(client, userdata, message):
    '''
    Transform Data and publish transformed data to publish topic
    '''
    start = millis()
    message_uuid = str(uuid.uuid4())
    #client.publish(root_topic + 'metrics/messages', json.dumps({'event': 'message-received', 'timestamp': millis(), 'message-uuid': message_uuid}))
    prompt = [
        SYSTEM_PROMPT,
        {'role': 'user', 'content': f'{config["user-prompt"]}\n\n{message.payload.decode()}' if config['user-prompt'] else f'{message.payload.decode()}'}
    ]

    chat_response = openai.ChatCompletion.create(
        model=config['chat-gpt-model'],
        messages=prompt,
        response_format={'type': 'json_object'}
    )

    response_content = chat_response['choices'][0]['message']['content']



    end = millis()
    response = {
        'uuid': message_uuid,
        'received-ts': start,
        'processed-ts': end,
        'response-content': response_content,
        'latency': end - start,
        **chat_response['usage']
    }
    client.publish(env.MQTT_PUBLISH_TOPIC, response_content)
    client.publish(root_topic+'metrics/message-processed', json.dumps(response))


def on_connect(client, userdata, flags, rc):
    if DEBUG:
        client.publish(log_topic, f'Client Connected: {env.MQTT_CLIENT_ID}')

    client.publish(root_topic+'metrics/STATE', 'ONLINE', retain=True)
    client.publish(root_topic+'config', json.dumps(config), retain=True)

    client.subscribe(env.MQTT_SUBSCRIBE_TOPIC)
    client.message_callback_add(env.MQTT_SUBSCRIBE_TOPIC, on_incoming_data)




def create_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(client_id=env.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)

    if env.MQTT_USE_TLS:
        client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED)

    client.username_pw_set(username=env.MQTT_USERNAME, password=env.MQTT_PASSWORD)

    client.will_set(topic=root_topic+'metrics/STATE', payload='OFFLINE', retain=True)

    client.on_connect = on_connect

    return client


mqtt_client = create_mqtt_client()


def start_app():
    mqtt_client.connect(host=env.MQTT_HOST, port=env.MQTT_PORT)
    mqtt_client.loop_forever()