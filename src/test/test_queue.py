from common import get_rbmq_configuraion, get_rbmq_connection, pub_request_to_rbmq, pub_response_to_rbmq
if __name__ == '__main__':
    print('Test Queue')
    mq_configfile = '/tmp/mq.json'
    mq_config = get_rbmq_configuraion(mq_configfile)
    mq_conn = get_rbmq_connection(mq_config)
    print(f'{mq_config}/ {mq_conn}')

    request_id = 'Request1'
    response_id = 'Request1'
    pub_request_to_rbmq(mq_conn, request_id,routing_key=mq_config['request_queue'])
    pub_response_to_rbmq(mq_conn, response_id,routing_key=mq_config['response_queue'])