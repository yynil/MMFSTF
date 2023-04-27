import threading
import pika
from common import form_amqp_url,get_rbmq_configuraion,get_rbmq_connection,pub_request_to_rbmq,pub_response_to_rbmq
if __name__ == '__main__':
    print('Test Queue')
    mq_configfile = '/tmp/mq.json'
    mq_config = get_rbmq_configuraion(mq_configfile)
    print(f'{mq_config}')
    conn = get_rbmq_connection(mq_config)
    while True:
        request_id = input('Enter request_id: ')
        if request_id == 'exit':
            break
        pub_request_to_rbmq(conn, request_id,routing_key=mq_config['request_queue'],exchange='req_exch')