from common import get_rbmq_configuraion, AsyncConsumer,MessageHandler,ReconnectingAsyncConsumer

class MyMessageHandler(MessageHandler):
    def handle_message(self, body):
        print(f'Got message: {body}')

if __name__ == '__main__':
    print('Test Queue')
    mq_configfile = '/tmp/mq.json'
    mq_config = get_rbmq_configuraion(mq_configfile)
    amqp_url = f"amqp://{mq_config['user']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/{mq_config['vhost']}"
    consumer = ReconnectingAsyncConsumer(amqp_url,exchange='req_exch', queue=mq_config['request_queue'], message_handler=MyMessageHandler())
    consumer.run()