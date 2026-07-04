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
            message = json.dumps(body).encode("utf-8")
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
                    body=message,
                    properties=pika.BasicProperties(
                        content_type="application/json", delivery_mode=2
                    ),
                )
                logger.info("published %s: %s", routing_key, body)
            finally:
                connection.close()
        except Exception:
            # The rental itself already succeeded — a lost event must never
            # fail the request, so log (the traceback says whether the cause
            # was the broker or a bad payload) and move on.
            logger.warning(
                "failed to publish event, dropped (routing_key=%s)", routing_key, exc_info=True
            )
