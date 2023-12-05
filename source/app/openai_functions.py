from app import env, logging
from sparkplug_node_app import helpers
import openai
from typing import List
import uuid

openai.api_key = env.OPENAI_API_KEY

gpt_models = openai.Model.list()['data']

def list_gpt_models(models = gpt_models) -> List[str]:
    return [m.id for m in models if m.id.startswith('gpt-')]


def create_chat(
        model: str,
        messages: List[dict],
        message_uuid: str = None,
        **chat_params
    ):
    '''
    Create a chatGPT response
    '''
    err_prefix = 'Could not process data: '

    if model not in list_gpt_models():
        logging.error(f'{err_prefix}invalid gpt model "{model}"!')
        return

    if not messages:
        logging.error(f'{err_prefix}no prompt given!')

    start = helpers.millis()
    message_uuid = message_uuid if message_uuid else str(uuid.uuid4())

    response_data = {
        'success': True,
        'uuid': message_uuid,
        'received-ts': start,
    }

    try:
        chat_response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            **chat_params
        )
        end = helpers.millis()
        response_data.update({
            'processed-ts': end,
            'response': chat_response.to_dict_recursive(),
            'process-time': end - start,
            **chat_response['usage']
        })

        return response_data
    except openai.error.InvalidRequestError as err:
        logging.error(f'{err_prefix}{err}')
        end = helpers.millis()
        response_data.update({
            'success': False,
            'error': str(err),
            'processed-ts': end,
            'process-time': end - start
        })
        return response_data