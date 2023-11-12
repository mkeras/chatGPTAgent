FROM python:3.10-alpine3.18

# Set working directory
WORKDIR /app-data

# Copy requirements and install dependencies
COPY requirements.txt /app-data/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY ./app /app-data/app/
COPY ./run.py /app-data/

# Run run.py when the container launches
CMD ["python", "run.py"]