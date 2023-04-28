import redis
import json
from .data import Request,Context,ContextType
def get_redis_config(config_file :str = '/tmp/redis.conf') -> dict:
    with open(config_file,'r') as fp:
        return json.load(fp)
    
def get_redis_conn(config :dict) -> redis.Redis:
    return redis.Redis(host=config['host'],port=config['port'])

def is_request_id_exists(rconn :redis.Redis,request_id :str) -> bool :
    #check if request_id exists in redis 
    return rconn.exists(request_id)

def put_request_to_redis(rconn :redis.Redis,request :Request,ttl :int = 300) -> bool:
    #put the request to redis
    bs = request.serialize()
    #convert bytearray to bytes
    bs = bytes(bs)
    return rconn.set(request.request_id,bs,ex=ttl)

def del_request_from_redis(rconn :redis.Redis,request_id :str) -> bool:
    #del the request from redis
    return rconn.delete(request_id)

def get_request_from_redis(rconn :redis.Redis,request_id :str,extend_ttl :int = 0) -> Request:
    #get the request from redis
    try:
        bs = rconn.get(request_id)
        #update the ttl
        #convert bytes to bytearray
        if extend_ttl > 0:
            rconn.expire(request_id,extend_ttl)
        bs = bytearray(bs)
        request = Request(None,None,None)
        request.deserialize(bs)
        return request
    except Exception as e:
        print(e)
        return None