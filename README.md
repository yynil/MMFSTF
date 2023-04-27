# MMFSTF

MMFSTF is a synomy of (Multi-Model Finite State Transducer Framework). It is a framework for building finite state transducers (FSTs) for natural language processing (NLP) tasks. It is designed to be modular and extensible. 

It's built on top of RabbitMQ as a message broker and it's asynchronous by nature. It's designed to be used in a distributed environment, but can also be used in a single machine.

# Architecture

The architecture of MMFSTF is :

![Architecture](https://raw.githubusercontent.com/yynil/MMFSTF/master/Architecture.png)

# Tasks

. **Create a runnable asyncronous runtime based on RabbitMQ** : Done
. **Create a langchain wrapper as a service** : TBD
. **Add a context aware requests dispatcher** : This is the core of FSTs. The contexts in cache decides the next service to be called. TBD