import argparse
from common import get_rbmq_configuraion, get_rbmq_connection, pub_request_to_rbmq, pub_response_to_rbmq,ReconnectingAsyncConsumer,RequestMessageHandler,Request,get_redis_config,Context,ContextType,put_request_to_redis
import logging

from langchain import LLMChain, PromptTemplate
from transformers import AutoTokenizer,AutoModelForCausalLM
from transformers import pipeline
from langchain.llms import HuggingFacePipeline

LOGGER_FORMAT = f'{__file__} %(asctime)s %(levelname)s %(message)s AT %(funcName)s'
logging.basicConfig(format=LOGGER_FORMAT,level=logging.INFO)
LOGGER = logging.getLogger(__file__)

class BasicLLMChainService(RequestMessageHandler):

    def __init__(self, redis_config: dict, mq_config: dict,chain_name :str,gather_all_contexts :bool = False,llm_chain : LLMChain = None) -> None:
        super().__init__(redis_config, mq_config)
        self.chain_name = chain_name
        self.gather_all_contexts = gather_all_contexts
        self.llm_chain = llm_chain

    def handle_request(self, request: Request) -> str:
        LOGGER.info(f'handle_request {request} in llm chain service')
        request_status = request.request_status
        splitted_status = request_status.split('|')
        last_round = int(splitted_status[1])
        request.request_status = f'{self.chain_name}|{last_round+1}'
        contexts = request.contexts
        def get_client_service_str(contexts, gather_all_contexts):
            history_chats = []
            for context in contexts:
                if context.context_type == ContextType.TEXT and (context.src == 'CLIENT' or context.src == 'SERVICE'):
                    history_chats.append(context.data.decode('utf-8'))
            if gather_all_contexts:
                return '\n'.join(history_chats)
            if len(history_chats) == 0:
                return ''
            return history_chats[-1]
        if len(contexts) == 0:
            request.add_context(Context(bytearray('Hello from LLM Service'.encode('utf-8')),ContextType.TEXT,'SERVICE'))
        else:
            last_round_str = get_client_service_str(contexts, self.gather_all_contexts)
            LOGGER.info(f'send {last_round_str} to llm chain {self.chain_name}')
            response_str = self.llm_chain.run(last_round_str)
            LOGGER.info(f'get response {response_str} from llm chain {self.chain_name}')
            request.add_context(Context(bytearray(response_str.encode('utf-8')),ContextType.TEXT,'SERVICE'))
        #get redis connection
        redis_conn = self.get_redis_conn()
        #put the request to redis
        put_request_to_redis(redis_conn,request)
        return self.mq_config['request_queue']
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mq_config', type=str, default='/tmp/mq.json', help='The configuration file for the message queue')
    parser.add_argument('--redis_config', type=str, default='/tmp/redis.conf', help='The redis configuration file')
    parser.add_argument('--service_queue_id', type=str, default=None, help='The Service Queue ID')
    parser.add_argument('--chain_name', type=str, default=None, help='The LLM Chain Name')
    parser.add_argument('--gather_all_contexts', action='store_true', help='Gather all contexts')
    parser.add_argument('--model_path', type=str, help='The model path')
    parser.add_argument('--trust_remote_code',action='store_true',help='Trust remote code')
    parser.add_argument('--device',type=str,default='cpu',help='The device to run the model on')

    args = parser.parse_args()

    if args.device.startswith('cuda'):
        LOGGER.info('Load model to GPU in fp16')
        model = AutoModelForCausalLM.from_pretrained(args.model_path,trust_remote_code=args.trust_remote_code).half().to(args.device)
    else:
        LOGGER.info(f'Load model to {args.device} ')
        model = AutoModelForCausalLM.from_pretrained(args.model_path,trust_remote_code=args.trust_remote_code).to(args.device)

    tokenizer = AutoTokenizer.from_pretrained(args.model_path,trust_remote_code=args.trust_remote_code)
    p = pipeline('text-generation',model=model,tokenizer=tokenizer,device=args.device)
    llm = HuggingFacePipeline(pipeline=p)
    template = """Translate the following Chinese to English: {chinese}
    Translation:"""
    prompt = PromptTemplate(template=template, input_variables=["chinese"])
    chain = LLMChain(llm=llm, prompt=prompt)

    mq_config = get_rbmq_configuraion(args.mq_config)
    redis_config = get_redis_config(args.redis_config)
    service_queue_id = args.service_queue_id
    chain_name = args.chain_name
    gather_all_contexts = args.gather_all_contexts
    amqp_url = f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"
    LOGGER.info(f'amqp_url {amqp_url}')
    dispatcher = BasicLLMChainService(redis_config,mq_config,chain_name,gather_all_contexts,llm_chain=chain)
    consumer = ReconnectingAsyncConsumer(amqp_url,exchange='req_exch', queue=service_queue_id, message_handler=dispatcher)
    consumer.run()