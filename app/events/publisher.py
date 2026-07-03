import json
import logging

import pika

from app.core.config import settings
from app.events.constants import EXCHANGE_NAME

logger = logging.getLogger(__name__)


CONNECTION_TIMEOUT_SECONDS = 2


class EventPublisher:
    def publish(self, routing_key: str, body: dict) -> None:
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            parameters.socket_timeout = CONNECTION_TIMEOUT_SECONDS
            connection = pika.BlockingConnection(parameters)
            try:
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
                )
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key=routing_key,
                    body=json.dumps(body).encode("utf-8"),
                    properties=pika.BasicProperties(
                        content_type="application/json", delivery_mode=2
                    ),
                )
                logger.info("published %s: %s", routing_key, body)
            finally:
                connection.close()
        except Exception:
            logger.warning(
                "rabbitmq unreachable, event dropped (routing_key=%s)", routing_key, exc_info=True
            )
