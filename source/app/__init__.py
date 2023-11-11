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
    'user-prompt': env.GPT_USER_PROMPT if env.GPT_USER_PROMPT else None,
    'output-json': env.OUTPUT_JSON
}


DEBUG = env.DEBUG

root_topic = f'gpt-transform-v1/{env.AGENT_NAME}/'

config_topic = root_topic + 'config'
log_topic = root_topic + 'metrics/logs/debug'


def publish_config(client: mqtt.Client):
    client.publish(config_topic, json.dumps({'timestamp': millis(), 'config': config}), retain=True)

def on_config_change(client, userdata, message):
    try:
        new_config = json.loads(message.payload.decode())
    except Exception as err:
        if DEBUG:
            client.publish(log_topic, json.dumps({'eventType': 'error', 'error': str(err), 'function': 'on_config_change(client, userdata, message)'}))
        return
    
    new_config = new_config.get('config')
    if not new_config:
        if DEBUG:
            client.publish(log_topic, json.dumps({'eventType': 'error', 'error': 'New Config Published without "config" key', 'function': 'on_config_change(client, userdata, message)'}))
        return
    
    config_changed = False
    try:
        for key, value in new_config.items():
            if key not in config.keys() or value == config[key]:
                # Ignore Keys that don't belong
                continue
            config[key] = value
            config_changed = True

    except Exception as err:
        if DEBUG:
            client.publish(log_topic, json.dumps({'eventType': 'error', 'error': str(err), 'function': 'on_config_change(client, userdata, message)'}))
        return

    if not config_changed:
        if DEBUG:
            client.publish(log_topic, json.dumps({'eventType': 'log', 'message': 'new unchanged config received', 'function': 'on_config_change(client, userdata, message)'}))
        return
    
    publish_config(client)


def on_incoming_data(client, userdata, message):
    '''
    Transform Data and publish transformed data to publish topic
    '''
    start = millis()
    message_uuid = str(uuid.uuid4())
    
    prompt = [
        SYSTEM_PROMPT,
        {'role': 'user', 'content': f'{config["user-prompt"]}\n\n{message.payload.decode()}' if config['user-prompt'] else f'{message.payload.decode()}'}
    ]

    chat_params = dict(
        model=config['chat-gpt-model'],
        messages=prompt
    )

    if config['output-json']:
        chat_params['response_format'] = {'type': 'json_object'}

    chat_response = openai.ChatCompletion.create(**chat_params)

    response_content = chat_response['choices'][0]['message']['content']

    end = millis()
    response = {
        'uuid': message_uuid,
        'received-ts': start,
        'processed-ts': end,
        'response-content': response_content,
        'process-time': end - start,
        **chat_response['usage']
    }
    client.publish(env.MQTT_PUBLISH_TOPIC, response_content)
    client.publish(root_topic+'metrics/message-processed', json.dumps(response))


def on_connect(client, userdata, flags, rc):
    client.publish(root_topic+'metrics/STATE', b'', retain=True)
    client.publish(root_topic+'metrics/status', json.dumps({'state': 'ONLINE', 'ts': millis()}), retain=True)
    if DEBUG:
        client.publish(log_topic, f'Client Connected: {env.AGENT_NAME}')

    client.message_callback_add(env.MQTT_SUBSCRIBE_TOPIC, on_incoming_data)
    client.message_callback_add(config_topic, on_config_change)

    client.subscribe(config_topic)
    client.subscribe(env.MQTT_SUBSCRIBE_TOPIC)

    publish_config(client)
    


def create_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(client_id=env.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)

    if env.MQTT_USE_TLS:
        client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED)

    client.username_pw_set(username=env.MQTT_USERNAME, password=env.MQTT_PASSWORD)

    client.will_set(topic=root_topic+'metrics/STATE', payload=json.dumps({'state': 'OFFLINE', 'will-set-ts': millis()}), retain=True)

    client.on_connect = on_connect

    return client



def start_app():
    mqtt_client = create_mqtt_client()
    mqtt_client.connect(host=env.MQTT_HOST, port=env.MQTT_PORT)
    mqtt_client.loop_forever()