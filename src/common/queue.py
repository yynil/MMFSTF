import functools
import json
import pika
from .data import Request, Context, ContextType
import logging
import time
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

from pika.exchange_type import ExchangeType

def get_rbmq_configuraion(config_file :str = '/tmp/mq.json') -> dict:
    with open(config_file,'r') as fp:
        return json.load(fp)
    
def get_rbmq_connection(config :dict) -> pika.BlockingConnection:
    #TODO::add a connection pool support 
    credentials = pika.PlainCredentials(config['user'], config['password'])
    parameters = pika.ConnectionParameters(config['host'], config['port'], config['vhost'], credentials,heartbeat=600,blocked_connection_timeout=300)
    return pika.BlockingConnection(parameters)


def pub_request_to_rbmq(conn :pika.BlockingConnection,request_id :str,exchange :str = 'req_exch',routing_key :str = 'Request_Queue') -> bool:
    #pub the request to rbmq
    try:
        channel = conn.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='topic')
        channel.confirm_delivery()
        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=request_id)
        return True
    except Exception as e:
        print(e)
        return False
    
def pub_response_to_rbmq(conn :pika.BlockingConnection,request_id :str,exchange :str = 'req_exch',routing_key :str = 'Response_Queue') -> bool:
    #pub the request to rbmq
    return pub_request_to_rbmq(conn,request_id,exchange,routing_key)


def form_amqp_url(mq_config):
    return f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"