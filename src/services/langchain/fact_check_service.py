import argparse
from common import get_rbmq_configuraion, get_rbmq_connection, pub_request_to_rbmq, pub_response_to_rbmq,ReconnectingAsyncConsumer,RequestMessageHandler,Request,get_redis_config,Context,ContextType,put_request_to_redis
import logging

from langchain import LLMChain, PromptTemplate
from transformers import AutoTokenizer,AutoModelForCausalLM
from langchain.llms import OpenAI

LOGGER_FORMAT = f'{__file__} %(asctime)s %(levelname)s %(message)s AT %(funcName)s'
logging.basicConfig(format=LOGGER_FORMAT,level=logging.INFO)
LOGGER = logging.getLogger(__file__)

class FactCheckService(RequestMessageHandler):

    def __init__(self, redis_config: dict, mq_config: dict) -> None:
        super().__init__(redis_config, mq_config)

    def handle_request(self, request: Request) -> str:
        LOGGER.info(f'handle_request {request} in fact check service')
        request_status = request.request_status
        splitted_status = request_status.split('|')
        last_round = int(splitted_status[1])
        request.request_status = f'FACT_CHECKER|{last_round+1}'
        contexts = request.contexts

        if len(contexts) == 0:
            request.add_context(Context(bytearray('Hello from FACT_CHECKER Service'.encode('utf-8')),ContextType.TEXT,'SERVICE'))
        else:
            ##This is just a fixed context which should be calculated by last_round_str embedddings and retrieved from a vector database
            context ="""
            1、刘备(161-223)，221年至223年在位。蜀汉照烈皇帝，字玄德，涿郡(今河北省涿县)人，汉景帝之子中山靖王刘胜的后代。少年时孤独贫困，与母亲贩鞋子、织草席为生，后与关羽、张飞于桃园结义为异姓兄弟。剿除黄巾军有功，任安喜县尉。经常寄人篱下，先后投靠过公孙瓒、陶谦、曹操、袁绍、刘表等。建安十二年(207)，徐庶荐举诸葛亮，刘备三顾茅庐请出诸葛亮为军师，率军攻占了荆州、益州、汉中。于公元221年正式称帝，定都成都，国号汉，年号章武，史称“蜀汉”。在替关羽、张飞报仇时，大举进攻吴国，被东吴陆逊用火攻打败，不久病死于白帝城，享年63岁。
            """
            request.add_context(Context(bytearray(context.encode('utf-8')),ContextType.TEXT,'SERVICE'))
        #get redis connection
        redis_conn = self.get_redis_conn()
        #put the request to redis
        put_request_to_redis(redis_conn,request)
        return self.mq_config['request_queue']
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mq_config', type=str, default='scripts/mq.json', help='The configuration file for the message queue')
    parser.add_argument('--redis_config', type=str, default='scripts/redis.conf', help='The redis configuration file')
    parser.add_argument('--service_queue_id', type=str, default=None, help='The Service Queue ID')

    args = parser.parse_args()


    mq_config = get_rbmq_configuraion(args.mq_config)
    redis_config = get_redis_config(args.redis_config)
    service_queue_id = args.service_queue_id
    amqp_url = f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"
    LOGGER.info(f'amqp_url {amqp_url}')
    dispatcher = FactCheckService(redis_config,mq_config)
    consumer = ReconnectingAsyncConsumer(amqp_url,exchange='req_exch', queue=service_queue_id, message_handler=dispatcher)
    consumer.run()