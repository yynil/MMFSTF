import pika
import argparse
from common import get_rbmq_configuraion, get_rbmq_connection, pub_request_to_rbmq, pub_response_to_rbmq,ReconnectingAsyncConsumer,RequestMessageHandler,Request,get_redis_config,Context,ContextType,put_request_to_redis
import logging
LOGGER_FORMAT = f'{__file__} %(asctime)s %(levelname)s %(message)s AT %(funcName)s'
logging.basicConfig(format=LOGGER_FORMAT,level=logging.INFO)
LOGGER = logging.getLogger(__file__)

class BasicResponseRequestHandler(RequestMessageHandler):
    def __init__(self, redis_config: dict, mq_config: dict) -> None:
        super().__init__(redis_config, mq_config)

    def handle_request(self, request: Request) -> str:
        LOGGER.info(f'handle_request {request}')
        request.add_context(Context(bytearray('Hello from RESPONSE_HANDLER'.encode('utf-8')),ContextType.TEXT,'RESPONSE_HANDLER'))
        request_status = request.request_status
        splitted_status = request_status.split('|')
        last_round = int(splitted_status[1])
        request.request_status = f'RESPONSE|{last_round+1}'
        #get redis connection
        redis_conn = self.get_redis_conn()
        #put the request to redis
        put_request_to_redis(redis_conn,request,ttl=60*10)
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mq_config', type=str, default='/tmp/mq.json', help='The configuration file for the message queue')
    parser.add_argument('--redis_config', type=str, default='/tmp/redis.conf', help='The request id')
    args = parser.parse_args()

    mq_config = get_rbmq_configuraion(args.mq_config)
    redis_config = get_redis_config(args.redis_config)
    amqp_url = f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"
    print(f'amqp_url {amqp_url}')
    dispatcher = BasicResponseRequestHandler(redis_config,mq_config)
    consumer = ReconnectingAsyncConsumer(amqp_url,exchange='req_exch', queue=mq_config['response_queue'], message_handler=dispatcher)
    consumer.run()