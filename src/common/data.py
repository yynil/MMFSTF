from enum import Enum
from typing import List

class ContextType(Enum):
    TEXT = 1
    IMAGE = 2
    AUDIO = 3

class Context:
    @property
    def src(self) -> str:
        return self._src
    @src.setter
    def src(self, src: str):
        self._src = src

    @property
    def data(self) -> bytearray:
        return self._data
    
    @data.setter
    def data(self, data: bytearray):
        self._data = data

    @property
    def context_type(self) -> ContextType:
        return self._context_type
    
    @context_type.setter
    def context_type(self, context_type: ContextType):
        self._context_type = context_type

    def __init__(self, data: bytearray, context_type: ContextType, src: str = None):
        self._data = data
        self._context_type = context_type
        if src is None:
            self._src = 'UNKNOWN'
        else:
            self._src = src

    def __str__(self):
        if self._context_type == ContextType.TEXT:
            return f"Context: {self._data.decode()} of type {self._context_type}，from {self._src}"
        return f"Context: {self._data} of type {self._context_type}，from {self._src}"
    
    def __repr__(self):
        return self.__str__()
    
    def serialize(self) -> bytearray:
        try:
            #serialize data and context_type to a bytearray
            bs = bytearray()
            #encode the len of the data with 2 bytes
            bs.extend(len(self._data).to_bytes(2, byteorder='big'))
            bs.extend(self._data)
            #encode the context_type with 1 byte
            bs.extend(self._context_type.value.to_bytes(1, byteorder='big'))
            #encode the src to bytes
            src_bs = self._src.encode('utf-8')
            #encode the len of the src with 2 bytes
            bs.extend(len(src_bs).to_bytes(2, byteorder='big'))
            #encode the src with bytes
            bs.extend(src_bs)
            return bs
        except Exception as e:
            print(e)
            return None
    def deserialize(self, data: bytearray) -> int:
        try:
            #deserialize data and context_type from a bytearray and return how many bytes were read
            offset = 0
            #get the len of the data
            data_len = int.from_bytes(data[offset:offset+2], byteorder='big')
            offset += 2
            #get the data
            self._data = data[offset:offset+data_len].copy()
            offset += data_len
            #get the context_type
            self._context_type = ContextType(int.from_bytes(data[offset:offset+1], byteorder='big'))
            offset += 1
            #get the len of the src
            src_len = int.from_bytes(data[offset:offset+2], byteorder='big')
            offset += 2
            #get the src bytes
            src_bs = data[offset:offset+src_len].copy()
            offset += src_len
            #decode the src bytes
            self._src = src_bs.decode('utf-8')
            return offset
        except Exception as e:
            print(e)
            return None

    def __eq__(self, other):
        return self._data == other._data and self._context_type == other._context_type and self._src == other._src
    

    
class Request:
    
    @property
    def request_id(self) -> str:
        return self._request_id
    
    @request_id.setter
    def request_id(self, request_id: str):
        self._request_id = request_id

    @property
    def request_status(self) -> str:
        return self._request_status
    
    @request_status.setter
    def request_status(self, request_status: str):
        self._request_status = request_status

    @property
    def contexts(self) -> List[Context]:
        return self._contexts
    
    @contexts.setter
    def contexts(self, contexts: List[Context]):
        self._contexts = contexts

    def add_context(self, context: Context):
        self._contexts.append(context)

    def __init__(self, request_id: str, request_status: str, contexts: List[Context]):
        self._request_id = request_id
        self._request_status = request_status
        self._contexts = contexts

    def __str__(self):
        return f"Request: {self._request_id} with status {self._request_status} and contexts {self._contexts}"
    def __repr__(self):
        return self.__str__()
    
    
    def serialize(self) -> bytearray:
        try:
            #serialize request_id, request_status and contexts to a bytearray
            bs = bytearray()
            req_id_bs = self._request_id.encode()
            #encode the len of the request_id with 2 bytes
            bs.extend(len(req_id_bs).to_bytes(2, byteorder='big'))
            bs.extend(req_id_bs)
            req_status_bs = self._request_status.encode()
            #encode the len of the request_status with 2 bytes
            bs.extend(len(req_status_bs).to_bytes(2, byteorder='big'))
            bs.extend(req_status_bs)
            #encode the number of contexts with 2 bytes
            bs.extend(len(self._contexts).to_bytes(2, byteorder='big'))
            for context in self._contexts:
                bs.extend(context.serialize())
            return bs
        except Exception as e:
            print(e)
            return None
    
    def deserialize(self, data: bytearray) -> int:
        try:
            #deserialize request_id, request_status and contexts from a bytearray
            offset = 0
            #get the len of the request_id
            req_id_len = int.from_bytes(data[offset:offset+2], byteorder='big')
            offset += 2
            #get the request_id
            self._request_id = data[offset:offset+req_id_len].decode()
            offset += req_id_len
            #get the len of the request_status
            req_status_len = int.from_bytes(data[offset:offset+2], byteorder='big')
            offset += 2
            #get the request_status
            self._request_status = data[offset:offset+req_status_len].decode()
            offset += req_status_len
            #get the number of contexts
            contexts_num = int.from_bytes(data[offset:offset+2], byteorder='big')
            offset += 2
            #get the contexts
            self._contexts = []
            for i in range(contexts_num):
                context = Context(None, None)
                offset += context.deserialize(data[offset:])
                self._contexts.append(context)
            return offset
        except Exception as e:
            print(e)
            return 0

    def __eq__(self, other):
        return self._request_id == other._request_id and self._request_status == other._request_status and self._contexts == other._contexts

    

    
