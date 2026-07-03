import json
import logging
import time

import pika

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.events.constants import EXCHANGE_NAME, QUEUE_NAME, RENTAL_ROUTING_PATTERN

setup_logging(logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

RECONNECT_DELAY_SECONDS = 5


def handle_message(channel, method, properties, body):
    routing_key = method.routing_key
    payload = json.loads(body)

    if routing_key == "rental.created":
        logger.info(
            "would send receipt to customer %s for rental %s",
            payload.get("customer"),
            payload.get("rental_id"),
        )
    elif routing_key == "rental.ended":
        logger.info(
            "would send rental-ended confirmation for rental %s", payload.get("rental_id")
        )
    else:
        logger.info("received unhandled event %s: %s", routing_key, payload)

    channel.basic_ack(delivery_tag=method.delivery_tag)


def run() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(
                queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key=RENTAL_ROUTING_PATTERN
            )
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=handle_message)

            logger.info("worker connected, consuming queue '%s'", QUEUE_NAME)
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("worker shutting down")
            break
        except Exception:
            logger.warning(
                "rabbitmq unreachable, retrying in %ss", RECONNECT_DELAY_SECONDS, exc_info=True
            )
            time.sleep(RECONNECT_DELAY_SECONDS)


if __name__ == "__main__":
    run()
