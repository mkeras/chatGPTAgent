# chatGPTAgent
## Overview
This container is conceptualized to function as a part of a UNS, connecting to an MQTT Broker as both a consumer and producer of events/information. It subscribes to a specified MQTT topic, processes incoming messages using a specified ChatGPT model and prompt, and then publishes the results to another topic. The container can be used independently or orchestrated in a sequence where one instance's output becomes the input for the next, enabling complex step by step data transformations. Another setup could be having 1 container manipulate the prompt settings of another (Have the output topic of one instance be the config topic of another instance), etc.

## Development Status
- Under active development: Subject to significant changes as features are added and refined.
- Expanding capabilities: Future updates will include more complex functions like function calling and automating of prompt container chaining.

## Configuration
Environment variables are used for configuration:

- DEBUG: Enable debugging (e.g., true or false). Publish logs/error to the logs/debug topic.
- OPENAI_API_KEY: Your OpenAI API Key
- GPT_MODEL: GPT model identifier (e.g., gpt-3.5-turbo); typos can cause crashes. See https://platform.openai.com/docs/models
- GPT_SYSTEM_PROMPT: System prompt for the model
- GPT_USER_PROMPT: Optional user prompt added before incoming messages
- OUTPUT_JSON: Format of output (true/false; refer to OpenAI API documentation (https://platform.openai.com/docs/api-reference/chat/create#chat-create-response_format))
- MQTT Variables:
    - MQTT_SUBSCRIBE_TOPIC: Topic to subscribe to (e.g., testing/chatGPTAgent/events/INCOMING-TEST)
    - MQTT_PUBLISH_TOPIC: Topic to publish results (e.g., testing/chatGPTAgent/events/OUTGOING-TEST)
    - MQTT_HOST: MQTT Broker Address/IP
    - MQTT_PORT: Port for MQTT (1883 or 8883 for SSL)
    - MQTT_USE_TLS: Use SSL (true/false)
    - MQTT_USERNAME: MQTT username
    - MQTT_PASSWORD: MQTT password
    - MQTT_CLIENT_ID: MQTT Client ID (auto-set if left empty)
- AGENT_NAME: Name for the agent, used in config and metrics topics (defaults to MQTT_CLIENT_ID)

## Topic Structure
The MQTT_SUBSCRIBE_TOPIC is the topic which will be fed into chatGPT. The MQTT_PUBLISH_TOPIC is where the resulting content from chatGPT will be published to.
For now, the topic structure that the container uses is:
- gpt-transform-v1/<AGENT_NAME>/metrics/status --> The online/offline status of the container instance. Retained Message.
- gpt-transform-v1/<AGENT_NAME>/config --> The config dict of the chatGPT settings. Retained Message.
- gpt-transform-v1/<AGENT_NAME>/metrics/message-processed --> The metrics published on every message processed. Includes token usage and the content that was published to the MQTT_PUBLISH_TOPIC. Retained Message
- gpt-transform-v1/<AGENT_NAME>/metrics/logs/debug --> Topic where messages are published when DEBUG env var is set to true.

## Features
- Process/Transform data from an MQTT topic and publish it to another MQTT topic
- Change chatGPT configuration parameters via MQTT. Right now this topic is overwritten whenever by the environment variables whenever the container starts, but it will be updated to default to the config stored in the MQTT config topic, if available.