FROM mkult1a/sparkplug-node:dev


ENV SPARKPLUG_GROUP_ID='chatGPT Agents'
ENV GPT_MODEL=gpt-4-1106-preview

COPY requirements.txt /app-data/requirements2.txt
RUN pip install --no-cache-dir -r /app-data/requirements2.txt

COPY ./app /sparkplug-node/app/

CMD ["python", "-m", "app"]