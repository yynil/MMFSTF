import argparse
from common import get_rbmq_configuraion, get_rbmq_connection, pub_request_to_rbmq, pub_response_to_rbmq,ReconnectingAsyncConsumer,RequestMessageHandler,Request,get_redis_config,Context,ContextType,put_request_to_redis
import logging

from langchain import LLMChain, PromptTemplate
from transformers import AutoTokenizer,AutoModelForCausalLM
from langchain.llms import OpenAI

LOGGER_FORMAT = f'{__file__} %(asctime)s %(levelname)s %(message)s AT %(funcName)s'
logging.basicConfig(format=LOGGER_FORMAT,level=logging.DEBUG)
LOGGER = logging.getLogger(__file__)

class BasicLLMChainService(RequestMessageHandler):

    def __init__(self, redis_config: dict, mq_config: dict,llm_chain : LLMChain = None) -> None:
        super().__init__(redis_config, mq_config)
        self.llm_chain = llm_chain

    def handle_request(self, request: Request) -> str:
        LOGGER.info(f'handle_request {request} in llm chain service')
        request_status = request.request_status
        splitted_status = request_status.split('|')
        last_round = int(splitted_status[1])
        request.request_status = f'OPEN_AI_ANSWER|{last_round+1}'
        contexts = request.contexts
        if len(contexts) == 0:
            request.add_context(Context(bytearray('Hello from LLM Service'.encode('utf-8')),ContextType.TEXT,'SERVICE'))
        else:
            #get the last round str from contexts which is not from dispatcher
            last_round_str = None
            last_round_question = None
            for context in reversed(contexts):
                if context.src == 'SERVICE':
                    last_round_str = context.data.decode('utf-8')
                if context.src == 'CLIENT':
                    last_round_question = context.data.decode('utf-8')
                if last_round_str is not None and last_round_question is not None:
                    break

            if last_round_str is None or last_round_question is None:
                request.add_context(Context(bytearray('No question/context found'.encode('utf-8')),ContextType.TEXT,'SERVICE'))
                return self.mq_config['request_queue']
            LOGGER.debug(f'send {last_round_question} at {last_round_str} to OPENAI')
            response_str = self.llm_chain.run(Context=last_round_str,Question=last_round_question)
            LOGGER.debug(f'get response {response_str} from OPENAI')
            request.add_context(Context(bytearray(response_str.encode('utf-8')),ContextType.TEXT,'SERVICE'))
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

    llm = OpenAI()


    template = """请根据上下文回答问题。\n
    上下文：{Context}\n
    问题：{Question}\n
    让我们一步一步思考。\n
    回答：
    """
    prompt = PromptTemplate(template=template, input_variables=["Context", "Question"])
    chain = LLMChain(llm=llm, prompt=prompt)

    mq_config = get_rbmq_configuraion(args.mq_config)
    redis_config = get_redis_config(args.redis_config)
    service_queue_id = args.service_queue_id
    amqp_url = f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"
    LOGGER.info(f'amqp_url {amqp_url}')
    dispatcher = BasicLLMChainService(redis_config,mq_config,llm_chain=chain)
    consumer = ReconnectingAsyncConsumer(amqp_url,exchange='req_exch', queue=service_queue_id, message_handler=dispatcher)
    consumer.run()