from common import Context, ContextType, Request

if __name__ == "__main__":
    #create an array of contexts
    contexts = []
    contexts_num = 10
    for i in range(contexts_num):
        text_array = bytearray(f'Text{i}'.encode())
        contexts.append(Context(text_array, ContextType(i%3+1)))
    #create a request
    request = Request("Request1", "Status1", contexts)
    print(f'{request}')
    #serialize the request
    bs = request.serialize()
    print(f'Serialized bs length: {len(bs)}')
    #deserialize the request
    request2 = Request(None, None, None)
    request2.deserialize(bs)
    print(f'{request2}')
    #compare the two requests
    print(f'Are the two requests equal? {request == request2}')