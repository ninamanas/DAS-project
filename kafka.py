from confluent_kafka import Producer

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
TOPIC_NAME = 'stock_data'

# Create Kafka Producer
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'stock_producer'
})

# Example Data
data = {'symbol': 'AAPL', 'price': 150.0}

# Send Data to Kafka Topic
producer.produce(TOPIC_NAME, value=str(data).encode('utf-8'))

# Ensure all messages are delivered before terminating
producer.flush()
