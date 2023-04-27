import base64
from fastapi import FastAPI
import uuid
from common import get_redis_config,get_redis_conn,put_request_to_redis,get_request_from_redis,is_request_id_exists,\
    Request,Context,ContextType,get_rbmq_configuraion,get_rbmq_connection,pub_request_to_rbmq,del_request_from_redis
import logging
LOGGER_FORMAT = f'{__name__} %(asctime)s %(levelname)s %(message)s' 
logging.basicConfig(format=LOGGER_FORMAT,level=logging.INFO)
LOGGER = logging.getLogger(__name__)

redis_conf = get_redis_config()
rbmq_conf = get_rbmq_configuraion()

app = FastAPI()

@app.get("/conversation")
async def conversation(request_id :str = None,data_type :str = 'TEXT',data :str = None):
    if data is None:
        return {"message": "data is None", "request_id": request_id}
    if request_id is None:
        #init a new conversation, generate a new request_id with uuid
        request_id = str(uuid.uuid4())
    
    #create a new context
    if data_type is None or data_type.upper() == 'TEXT':
        context_type = ContextType.TEXT
        #convert data string to bytearray
        data = bytearray(data.encode('utf-8'))
    elif data_type.upper() == 'IMAGE':
        context_type = ContextType.IMAGE
        #convert base64 string data to bytearray
        data = bytearray(base64.b64decode(data))
    elif data_type.upper() == 'AUDIO':
        context_type = ContextType.AUDIO
        #convert base64 string data to bytearray
        data = bytearray(base64.b64decode(data))
    else:
        return {"message": f"data_type {data_type} is not supported", "request_id": request_id}
    
    redis_conn = get_redis_conn(redis_conf)
    
    context = Context(data,context_type,src = 'CLIENT')

    if is_request_id_exists(redis_conn,request_id):
        #get the request from redis
        request = get_request_from_redis(redis_conn,request_id)
        status = request.request_status
        splitted_status = status.split('|')
        current_status = splitted_status[0]
        current_round = int(splitted_status[1])
        if current_status == 'CLIENT':
            redis_conn.close()
            return {"message": "Please wait for response patiently", "request_id": request_id}
        LOGGER.info(f'current_status {current_status},current_round {current_round}')
        new_status = 'CLIENT|'+str(current_round+1)
        LOGGER.info(f'new_status {new_status}')
        request.request_status = new_status
    else:
        #put the request to redis
        status = 'CLIENT|0'#status is to record current conversation status, format is 'status|current_conversation_round'
        request = Request(request_id,status,[])
        new_status = status
    request.contexts.append(context)

    put_request_to_redis(redis_conn,request,ttl = 60*1)
    LOGGER.info(f'current request {request} to redis')

    #pub the request to rbmq
    rbmq_conn = get_rbmq_connection(rbmq_conf)
    num_retries = 3
    succ = False
    while num_retries > 0 and not succ:
        LOGGER.info(f'pub request {request} to rbmq')
        succ = pub_request_to_rbmq(rbmq_conn,request.request_id,routing_key=rbmq_conf['request_queue'],exchange='req_exch')
        num_retries -= 1

    if not succ:
        #if pub to rbmq failed, reverse the request status
        if new_status == 'CLIENT|0':
            #delete the request since it is a new request
            LOGGER.info(f'delete request {request} from redis')
            del_request_from_redis(redis_conn,request_id)
        else:
            request.request_status = status
            request.contexts = request.contexts[:-1]
            put_request_to_redis(redis_conn,request,ttl = 60*1)
            LOGGER.info(f'current request {request} to redis')
    rbmq_conn.close()
    redis_conn.close()
    return {"message": succ, "request_id": request_id}

def convert_request_to_json(request):
    json_dict = {}
    json_dict['request_id'] = request.request_id
    json_dict['request_status'] = request.request_status
    json_dict['contexts'] = []
    for context in request.contexts:
        context_json = {}
        context_json['context_type'] = context.context_type.name
        context_json['src'] = context.src
        if context.context_type == ContextType.TEXT:
            context_json['data'] = context.data.decode('utf-8')
        elif context.context_type == ContextType.IMAGE:
            context_json['data'] = base64.b64encode(context.data).decode('utf-8')
        elif context.context_type == ContextType.AUDIO:
            context_json['data'] = base64.b64encode(context.data).decode('utf-8')
        json_dict['contexts'].append(context_json)
    return json_dict

@app.get("/conversation/{request_id}")
async def get_conversation(request_id :str):
    redis_conn = get_redis_conn(redis_conf)
    if not is_request_id_exists(redis_conn,request_id):
        return {"message": "request_id not exists", "request_id": request_id}
    request = get_request_from_redis(redis_conn,request_id)
    return {"message": convert_request_to_json(request), "request_id": request_id}

