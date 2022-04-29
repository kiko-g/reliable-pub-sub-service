import time
import zmq
from logger import Logger
from clients_list_record import ClientListRecord
from message import Message
from message_factory import MessageFactory
from message_list_record import MessageListRecord
from storage import Storage
from utils import *

interval_timeout = 3
context = zmq.Context()


class Proxy:
    def __init__(self, xpub_port: int = 5555, xsub_port: int = 5556, rep_port: int = 6789) -> None:
        self.retransmission_interval = 5
        self.xpub_address = f'tcp://127.0.0.1:{xpub_port}'
        self.xsub_address = f'tcp://127.0.0.1:{xsub_port}'
        self.rep_address = f'tcp://127.0.0.1:{rep_port}'

        self.storage = Storage()
        self.clients, self.messages = self.storage.load()

        # create XPUB
        self.xpub_socket = context.socket(zmq.XPUB)
        self.xpub_socket.bind(self.xpub_address)

        # create XSUB
        self.xsub_socket = context.socket(zmq.XSUB)
        self.xsub_socket.bind(self.xsub_address)

        # create REP
        self.rep_socket = context.socket(zmq.REP)
        self.rep_socket.bind(self.rep_address)

        # create poller
        self.poller = zmq.Poller()
        self.poller.register(self.xpub_socket, zmq.POLLIN)
        self.poller.register(self.xsub_socket, zmq.POLLIN)
        self.poller.register(self.rep_socket, zmq.POLLIN)

    def __str__(self):
        return 'Proxy'

    '''
    Periodic Alarm to Retransmit and delete already Ack MSGs
    '''

    def handler(self):
        for topic in self.messages.keys():
            to_delete = []
            for message_id in self.messages[topic].keys():
                if not self.messages[topic][message_id].clients_unacked:
                    to_delete.append(message_id)
                else:
                    if time.time() - self.messages[topic][
                        message_id].message.header.timestamp > self.retransmission_interval:
                        for client_unacked_id in self.messages[topic][message_id].clients_unacked:
                            self.retransmit(topic, message_id, self.messages[topic][message_id].message.body,
                                            client_unacked_id)

            for msg_id in to_delete:
                Logger.info(f'Deleting msg {msg_id} all clients ACK-ed!')
                del self.messages[topic][msg_id]

            if len(to_delete) > 0:
                Logger.info(f'Content of messages after delete: {self.messages}')

    '''
    End Periodic Handler
    '''

    def storage_handler(self):
        self.storage.save(self.clients, self.messages)

    def retransmit(self, topic: str, message_id, message_body: str, client_id: str):
        Logger.log(
            f'Retransmitting to client {client_id} about topic {topic}')
        # create REQ
        if topic not in self.clients.keys():
            Logger.warning(
                f'[BROKER] Retransmit for topic not exist. Maybe Unsubscribed?: Message Id{message_id} For Topic: {topic} Client: {client_id}')
            return

        if client_id not in self.clients[topic].keys():
            Logger.warning(
                f'[BROKER] Retransmit for client not exist. Maybe Unsubscribed?: Message Id{message_id} For Topic: {topic} Client: {client_id}')
            return

        req_socket = context.socket(zmq.REQ)

        req_socket.connect(self.clients[topic][client_id].client_address)
        req_socket.send_pyobj(MessageFactory.create_retransmission_message(topic, message_id, message_body))
        self.process_ack_received_msg(req_socket.recv_pyobj())
        req_socket.close()

    '''
    Mega Switch to Forward REP Messages to The correct function depending on message type 
    '''

    def process_rep_message(self, message: Message) -> None:
        if message.header.msg_type == 'hello':
            self.process_welcome_msg(message)
            return
        if message.header.msg_type == 'goodbye':
            self.process_goodbye_msg(message)
            return
        if message.header.msg_type == 'ack_received':
            self.process_ack_received_msg(message)
            self.rep_socket.send_pyobj(MessageFactory.create_dummy_ok_msg())
            return

        Logger.warning(f'Warning: Invalid Message. Not Processed')

    '''
    REP Messages
    '''

    def process_welcome_msg(self, message: Message) -> None:
        Logger.log(
            f'[BROKER] REP socket received Hello Msg From: {message.header.id_origin} For Topic: {message.header.topic}')
        self.rep_socket.send_pyobj(MessageFactory.create_ack_welcome_reply())
        Logger.log(f'[BROKER] REP Replied with ACK_Hello To: {message.header.address_origin}')

        '''
        If There isn't that topic, create new topic
        '''
        if message.header.topic not in self.clients.keys():
            Logger.log(f'[BROKER] Created New Topic {message.header.topic}')
            self.clients[message.header.topic] = {}

        Logger.log(
            f'[BROKER] Created New Client Record for Client: {message.header.id_origin} For Topic: {message.header.topic}')
        self.clients[message.header.topic][message.header.id_origin] = ClientListRecord(message.header.id_origin,
                                                                                        message.header.address_origin,
                                                                                        message.header.timestamp)

    def process_goodbye_msg(self, message: Message):

        if message.header.topic not in self.clients.keys():
            Logger.error(f'[BROKER] Received Goodbye for nonexistent topic {message.header.topic}')

        else:
            if message.header.id_origin not in self.clients[message.header.topic].keys():
                Logger.error(f'[BROKER] Received Goodbye for nonexistent client_record {message.header.id_origin}')
            else:
                del self.clients[message.header.topic][message.header.id_origin]
                Logger.info(
                    f'[BROKER] Removed Entry for client {message.header.id_origin} in Topic:{message.header.topic}')

        self.rep_socket.send_pyobj(MessageFactory.create_ack_goodbye_reply())

    def process_ack_received_msg(self, message: Message) -> None:
        if message.header.topic not in self.messages:
            Logger.warning(f'Warning Received ACK for unknown topic {message.header.topic}')
            Logger.info(f'Topics available: {self.messages}')
            return

        if message.header.message_id not in self.messages[message.header.topic]:
            Logger.warning(f'Warning Received ACK for unknown message')
            return

        for client_id in self.messages[message.header.topic][message.header.message_id].clients_unacked:
            if client_id == message.header.id_origin:
                self.messages[message.header.topic][message.header.message_id].clients_unacked.remove(client_id)
                Logger.log(
                    f'Received Valid ACK from: {message.header.id_origin} For Topic: {message.header.topic} MSG_ID {message.header.message_id}')
                Logger.divider()
                return

        Logger.error(
            f'[BROKER] Invalid Origin FOR ACK FROM: {message.header.id_origin}  For Topic: {message.header.topic}  MSG_ID: {message.header.message_id}')

    '''
    End REP Socket Messages
    '''

    '''
    PUB/SUB Messages
    '''

    def process_message_from_server(self, raw_message) -> None:
        message = MessageFactory.create_topic_message(raw_message[0], raw_message[1], raw_message[2])
        if message.header.topic not in self.messages:
            Logger.log(f'[BROKER] Created New Topic: {message.header.topic}')
            self.messages[message.header.topic] = {}

        list_clients = list_clients_existent_at_give_time_for_give_topic(message.header.topic, self.clients)
        self.messages[message.header.topic][message.header.message_id] = MessageListRecord(message, list_clients)
        Logger.log(
            f'[BROKER] Created New Message Record MSG:ID{message.header.message_id} Clients To ACK {list_clients}')

        # Forward To Subscribers
        self.xpub_socket.send_multipart(raw_message)
        Logger.log(f'[BROKER] Forward MSG:ID{message.header.message_id} To Subscribers')

    '''
    End PUB/SUB Messages
    '''

    def run(self) -> None:
        Logger.success(f'[BROKER] {self} running')

        set_interval(self.handler, True, interval_timeout)
        set_interval(self.storage_handler, True, interval_timeout)

        Logger.info(f'[BROKER] Interval Installed with Interval: {interval_timeout}')

        while True:
            event = dict(self.poller.poll())

            if self.xpub_socket in event:
                # Logger.divider()
                message = self.xpub_socket.recv_multipart()
                Logger.log(f'[BROKER] xPUB socket received msg: {message}')
                self.xsub_socket.send_multipart(message)
                Logger.info(f'[BROKER] xSub socket Forward msg: {message}')
                Logger.divider()

            elif self.xsub_socket in event:
                # Logger.divider()
                message = self.xsub_socket.recv_multipart()
                Logger.info(f'[BROKER] xSUB socket received msg: {message}')
                self.process_message_from_server(message)
                Logger.divider()

            elif self.rep_socket in event:
                # Logger.divider()
                message = self.rep_socket.recv_pyobj()
                self.process_rep_message(message)
                Logger.divider()

            else:
                Logger.error(f'Invalid Event')


if __name__ == '__main__':
    Proxy().run()
