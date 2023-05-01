# Dependancy Installation

Currently MMFSTF depends on RabbitMQ(as a message broker) and Redis(as a request/response data cache). You can install them by following the instructions below.

## RabbitMQ

1. Install RabbitMQ following the instructions [here](https://www.rabbitmq.com/download.html).
2. Import the RabbitMQ with our configuration file by running the following command with root privileges:

```bash
rabbitmqctl import_definitions scripts/default.rabbitmq.json
```

You can modify the configuration file to your needs. But remember the mmfst_user is our default user to connect to RabbitMQ. The original password is 39re02fjowfih3wf9, if you wanna change the default password, please update the hashed password in the configuration file. You can generate the hashed password by running the following command:

```bash
rabbitmqctl password_hash <your password>
```
The default vhost we use is /mmfstf. If you wanna change it, please update the configuration file accordingly.

The MMFSTF's message broker configuraiton file is scripts/mq.json. You can update the values you specified accordingly including vhost,user,password,ip and port.

For more information about RabbitMQ configuration, please refer to [this](https://www.rabbitmq.com/configure.html).

## Redis

1. Install Redis following the instructions [here](https://redis.io/docs/getting-started/installation/).
2. Enable Redis remote access by modifying the configuration file. The configuration file is usually located at /etc/redis/redis.conf. You can find the bind option and change it to the address you want to bind. Following the instructions [here](https://redis.io/topics/security) to enable Redis authentication. You can also change the default port to the one you want to use.
3. The MMFSTF's Redis configuration file is scripts/redis.json. You can update the values you specified accordingly including host, and port. Currently we skip the authentication part. If you want to enable it, feel free to update the configuration file and src/common/cache.py accordingly.

