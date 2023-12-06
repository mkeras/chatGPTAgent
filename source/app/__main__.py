from app import env, logging
from sparkplug_node_app import sparkplug, mqtt_functions, helpers
from app.chat_gpt_metrics import chat_metrics, get_create_chat_args
from app.openai_functions import create_chat
import paho.mqtt.client as mqtt
from functools import partial
from typing import Optional, Callable
import json


GLOBAL_DATA = {
    'SPARKPLUG_NODE': None,
    'MQTT_CLIENT': None,
    'MQTT_SUBSCRIBE_TOPIC': None,
    'MQTT_PUBLISH_TOPIC': None,
    'CHATGPT_OPTIONS': {

    }
}

"""
read function signature: read_function(prev_value)
returns value, whatever its datatype is

write function signature: write_function(value) -> bool
The bool return value of write indicates success / failure
"""

def validate_config_read() -> bool:
    """
    Validates all config to make sure it is ready to process and publish incoming messages
    """
    raise NotImplementedError


def on_incoming_message(client: mqtt.Client, userdata, message):
    process_message_start = helpers.millis()
    logging.debug('Message received for processing by chatGPT!')
    if not chat_gpt_system_prompt.current_value:
        logging.error(f'Unable to process message: "{chat_gpt_system_prompt.name}" is unset!')
        return

    payload = message.payload.decode()
    user_prompt = f'{chat_gpt_user_prompt.current_value}\n\n{payload}' if chat_gpt_user_prompt.current_value else f'{payload}'
    # Process message with chatGPT
    create_chat_args = dict(
        messages=[
            {'role': 'system', 'content': chat_gpt_system_prompt.current_value},
            {'role': 'user', 'content': user_prompt}
        ],
        **get_create_chat_args()
    )
    logging.debug('')
    logging.debug('')
    logging.debug(f'{create_chat_args}')
    logging.debug('')
    logging.debug('')

    result = create_chat(
        **create_chat_args
    )

    process_message_end = helpers.millis()
    if not result['success']:
        failed_count = chat_gpt_messages_processed_failed.current_value + 1
        chat_gpt_messages_processed_failed.update_value(failed_count)
        chat_gpt_last_message_processed_ts.update_value(process_message_end)
        if not chat_gpt_first_message_processed_ts.current_value:
            chat_gpt_first_message_processed_ts.update_value(process_message_end)
        return

    content = result['response']['choices'][0]['message']['content']
    client.publish(topic=mqtt_output_topic_tag.current_value, payload=content)

    if create_chat_args.get('response_format') and create_chat_args['response_format'].get('type') == 'json_object':
        result['response']['choices'][0]['message']['content'] = json.loads(content)

    total_tokens = chat_gpt_total_tokens.current_value + result['total_tokens']
    prompt_tokens = chat_gpt_prompt_tokens.current_value + result['prompt_tokens']
    completion_tokens = chat_gpt_completion_tokens.current_value + result['completion_tokens']

    chat_gpt_total_tokens.update_value(total_tokens)
    chat_gpt_prompt_tokens.update_value(prompt_tokens)
    chat_gpt_completion_tokens.update_value(completion_tokens)

    processed_count = chat_gpt_messages_processed.current_value + 1
    chat_gpt_messages_processed.update_value(processed_count)

    chat_gpt_last_message_processed_ts.update_value(process_message_end)
    if not chat_gpt_first_message_processed_ts.current_value:
        chat_gpt_first_message_processed_ts.update_value(process_message_end)

    chat_gpt_message_processed_json.update_value(json.dumps(result))
    
    logging.debug(f'Successfully processed incoming message with chatGPT API')
    global GLOBAL_DATA
    sparkplug_node = GLOBAL_DATA.get('SPARKPLUG_NODE')
    if sparkplug_node:
        logging.debug('-------Forcing RBE update-------')
        sparkplug_node.force_rbe()
    


def on_set_client(node: sparkplug.SparkplugEdgeNode, mqtt_client: mqtt.Client):
    logging.debug('CALLBACK: on_set_client')
    global GLOBAL_DATA
    GLOBAL_DATA['MQTT_CLIENT'] = mqtt_client
    GLOBAL_DATA['SPARKPLUG_NODE'] = node


def on_mqtt_connect(node: sparkplug.SparkplugEdgeNode, mqtt_client: mqtt.Client):
    logging.debug('CALLBACK: on_mqtt_connect')
    global GLOBAL_DATA
    GLOBAL_DATA['MQTT_CLIENT'] = mqtt_client
    GLOBAL_DATA['SPARKPLUG_NODE'] = node

    on_write_output_topic(mqtt_output_topic_tag, mqtt_output_topic_tag.current_value, True)
    on_write_input_topic(mqtt_input_topic_tag, mqtt_input_topic_tag.current_value, True)



"""
on_read callback signature: on_read(metric_obj=self, current_value=value, success=success)
on_write callback signature: on_write(metric_obj=self, value_written=value, success=success)
"""
def on_write_input_topic(metric_obj, value_written, success):
    global GLOBAL_DATA
    mqtt_client = GLOBAL_DATA.get('MQTT_CLIENT')
    if mqtt_client is None:
        logging.error(f'Failed to process input topic change, mqtt client is unset!')
        return
    if not success:
        logging.error(f'Failed to process input topic change, write was unsuccessful')
        return
    prev_value = metric_obj.current_value
    if prev_value:
        mqtt_client.unsubscribe(prev_value)
        mqtt_client.message_callback_remove(prev_value)
    if value_written:
        mqtt_client.subscribe(value_written)
        mqtt_client.message_callback_add(value_written, on_incoming_message)
    logging.info(f'SUBSCRIBE TOPIC CHANGED TO "{value_written}" from "{prev_value}"')


def on_write_output_topic(metric_obj, value_written, success):
    global GLOBAL_DATA
    if GLOBAL_DATA['MQTT_CLIENT'] is None:
        logging.error(f'Failed to process output topic change, mqtt client is unset!')
        return
    if not success:
        logging.error(f'Failed to process output topic change, write was unsuccessful')
        return
    logging.debug(f'PUBLISH TOPIC CHANGED TO "{value_written}" from "{metric_obj.current_value}"')


mqtt_input_topic_tag = sparkplug.SparkplugMemoryTag(
    name='Agent Config/MQTT Subscribe Topic',
    datatype=sparkplug.SparkplugDataTypes.String,
    initial_value=env.MQTT_SUBSCRIBE_TOPIC ,
    writable=True,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=on_write_input_topic
)
GLOBAL_DATA['MQTT_SUBSCRIBE_TOPIC'] = mqtt_input_topic_tag.current_value


mqtt_output_topic_tag = sparkplug.SparkplugMemoryTag(
    name='Agent Config/MQTT Publish Topic',
    datatype=sparkplug.SparkplugDataTypes.String,
    initial_value=env.MQTT_PUBLISH_TOPIC,
    writable=True,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=on_write_output_topic
)
GLOBAL_DATA['MQTT_PUBLISH_TOPIC'] = mqtt_output_topic_tag.current_value


chat_gpt_system_prompt = sparkplug.SparkplugMemoryTag(
    name='Agent Config/System Prompt',
    datatype=sparkplug.SparkplugDataTypes.String,
    initial_value=env.GPT_SYSTEM_PROMPT,
    writable=True,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_user_prompt = sparkplug.SparkplugMemoryTag(
    name='Agent Config/User Prompt',
    datatype=sparkplug.SparkplugDataTypes.String,
    initial_value=env.GPT_USER_PROMPT,
    writable=True,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

"""
chatGPT usage metrics
"""

chat_gpt_messages_processed_failed = sparkplug.SparkplugMemoryTag(
    name='Metrics/Messages Processed Failed',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_messages_processed = sparkplug.SparkplugMemoryTag(
    name='Metrics/Messages Processed',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_total_tokens = sparkplug.SparkplugMemoryTag(
    name='Metrics/Total Token Usage',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_completion_tokens = sparkplug.SparkplugMemoryTag(
    name='Metrics/Completion Token Usage',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_prompt_tokens = sparkplug.SparkplugMemoryTag(
    name='Metrics/Prompt Token Usage',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_first_message_processed_ts = sparkplug.SparkplugMemoryTag(
    name='Metrics/First Message Processed ts',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=None,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_last_message_processed_ts = sparkplug.SparkplugMemoryTag(
    name='Metrics/Last Message Processed ts',
    datatype=sparkplug.SparkplugDataTypes.Int64,
    initial_value=0,
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

chat_gpt_message_processed_json = sparkplug.SparkplugMemoryTag(
    name='Metrics/Message Processed JSON',
    datatype=sparkplug.SparkplugDataTypes.String,
    initial_value='',
    writable=False,
    disable_alias=True,
    persistence_file=env.MEMORY_TAGS_FILEPATH,
    on_write=None
)

# update_value(value)

def start():

    brokers = [
        mqtt_functions.BrokerInfo(
            client_id=env.MQTT_CLIENT_ID,
            host=env.MQTT_HOST,
            port=env.MQTT_PORT,
            username=env.MQTT_USERNAME,
            password=env.MQTT_PASSWORD,
            primary=True,
            name='Primary Broker 1'
        )
    ]

    edge_node = sparkplug.SparkplugEdgeNode(
        group_id=env.SPARKPLUG_GROUP_ID,
        edge_node_id=env.SPARKPLUG_EDGE_NODE_ID,
        brokers=brokers,
        metrics=[
            mqtt_input_topic_tag,
            mqtt_output_topic_tag,
            chat_gpt_system_prompt,
            chat_gpt_user_prompt,
            chat_gpt_messages_processed_failed,
            chat_gpt_messages_processed,
            chat_gpt_total_tokens,
            chat_gpt_completion_tokens,
            chat_gpt_prompt_tokens,
            chat_gpt_first_message_processed_ts,
            chat_gpt_last_message_processed_ts,
            chat_gpt_message_processed_json,
            *chat_metrics
        ],
        scan_rate=5000,
        on_set_client=on_set_client,
        on_mqtt_connect=on_mqtt_connect,
        config_filepath=env.CONFIG_FILEPATH,
        config_save_rate=60000
    )
    
    edge_node.loop_forever()

start()