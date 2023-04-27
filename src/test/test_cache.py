from common import Context, ContextType, Request, get_config, get_redis_conn, is_request_id_exists, put_request_to_redis, get_request_from_redis

if __name__ == "__main__":
    config = get_config()
    rconn = get_redis_conn(config)
    #create an array of contexts
    contexts = []
    contexts_num = 10
    for i in range(contexts_num):
        text_array = bytearray(f'Text{i}'.encode())
        contexts.append(Context(text_array, ContextType(i%3+1)))
    #create a request
    request = Request("Request1", "Status1", contexts)
    print(f'{request}')
    #check if request_id exists in redis
    print(f'Is request_id exists? {is_request_id_exists(rconn, request.request_id)}')
    #put the request to redis
    put_request_to_redis(rconn, request)
    #get the request from redis
    request2 = get_request_from_redis(rconn, request.request_id)
    print(f'{request2}')
    #compare the two requests
    print(f'Are the two requests equal? {request == request2}')