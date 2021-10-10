import redis
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)

redis_instance = redis.StrictRedis.from_url(settings.BROKER_URL)


@shared_task
def write_usage_log(now, container, remote_addr):
    """
    Simple task to increment a usage count and log the invocation details
    :param now: The time of the view request
    :param container: The name of the machine running the app service
    :param remote_addr: The IP provided in the view's request headers
    :return: Number of uses of this task
    """
    counter = redis_instance.incr("use_counter")
    logger.info(f"Use {counter} at {now} from {remote_addr} container {container} ")
    return counter
