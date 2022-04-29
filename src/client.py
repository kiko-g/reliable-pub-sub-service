import hashlib
import random
import sys
from time import sleep

from zmq import UNSUBSCRIBE

from logger import Logger

import zmq

from message import Message
from message_factory import MessageFactory
from utils import get_random_topics, set_interval

context = zmq.Context()


class Client:
    def __init__(self, client_id: int, error_spawner: bool = False, topics: list = [], xpub_port: int = 5555,
                 rep_proxy_port: int = 6789) -> None:

        self.id = hashlib.md5(str(client_id).encode()).hexdigest()
        self.error_spawner = error_spawner
        self.topics = ['animals', 'weather', 'zip-codes']
        self.xpub_address = f'tcp://127.0.0.1:{xpub_port}'
        self.rep_address = f'tcp://127.0.0.1:{7000 + client_id}'

        self.rep_proxy_address = f'tcp://127.0.0.1:{rep_proxy_port}'

        self.sub_socket = context.socket(zmq.SUB)
        self.sub_socket.connect(self.xpub_address)

        self.rep_client_socket = context.socket(zmq.REP)
        self.rep_client_socket.bind(self.rep_address)

        self.poller = zmq.Poller()
        self.poller.register(self.sub_socket, zmq.POLLIN)
        self.poller.register(self.rep_client_socket, zmq.POLLIN)

        self.discard_msgs = False

        self.topics = topics

        self.topics_unsubscribed_on_purpose = []

        for topic in self.topics:
            self.subscribe(topic)

    def __str__(self):
        return 'Client ' + str(self.id) + ': [' + ', '.join(str(t) for t in self.topics) + ']'

    def get(self) -> None:
        event = dict(self.poller.poll())

        if self.sub_socket in event:
            raw_message = self.sub_socket.recv_multipart()
            if not self.discard_msgs:
                Logger.info(f'[CLIENT] Sub Socket {raw_message}')
                self.send_ack_received_successfully(raw_message)

        elif self.rep_client_socket in event:
            message = self.rep_client_socket.recv_pyobj()

            if self.discard_msgs:
                Logger.error(f'[CLIENT] Req Socket FAILING SENDING THRASH IN Retransmission_ACK: {message.header.message_id} Topic: {message.header.topic}')
                self.rep_client_socket.send_pyobj(MessageFactory.create_dummy_ok_msg())
                return

            Logger.info(
                f'[CLIENT] Req Socket Received Retransmission For msg: {message.header.message_id} Topic: {message.header.topic}')

            self.send_ack_received_successfully_after_retransmission(message)

            return

        else:
            Logger.error(f'Unknown socket. Error')

    def send_ack_received_successfully(self, message_received_raw: list) -> None:
        message = MessageFactory.create_ack_received_reply(self.id, message_received_raw[1], message_received_raw[0])
        Logger.log(f'[CLIENT] Send ACK_RECEIVED MSG')

        req_proxy_socket = context.socket(zmq.REQ)
        req_proxy_socket.connect(self.rep_proxy_address)
        req_proxy_socket.send_pyobj(message)
        req_proxy_socket.recv()
        req_proxy_socket.close()

    def send_ack_received_successfully_after_retransmission(self, message_received_obj: Message):
        message = MessageFactory.create_ack_received_reply_after_retransmission(self.id,
                                                                                message_received_obj.header.message_id,
                                                                                message_received_obj.header.topic)
        Logger.log(
            f'[CLIENT] Send ACK_RECEIVED MSG AFTER RETRANSMITTING Message {message_received_obj.header.message_id} Topic:{message.header.topic}')

        self.rep_client_socket.send_pyobj(message)

    def subscribe(self, topic: str) -> None:
        req_proxy_socket = context.socket(zmq.REQ)
        req_proxy_socket.connect(self.rep_proxy_address)

        # Send Hello
        req_proxy_socket.send_pyobj(MessageFactory.create_hello_message(self.id, self.rep_address, topic))
        Logger.log(f'[CLIENT] REQ Socket Hello Sent')

        # Waits ACK
        # Blocking Call Intended
        req_proxy_socket.recv_pyobj()
        Logger.log(f'[CLIENT] REQ Socket ACK_Hello RECEIVED')

        req_proxy_socket.close()

        Logger.warning(f'[CLIENT] SUB Socket Subscribed Topic: {topic}')

        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def unsubscribe(self, topic: str) -> None:

        req_proxy_socket = context.socket(zmq.REQ)
        req_proxy_socket.connect(self.rep_proxy_address)

        # Send Hello
        req_proxy_socket.send_pyobj(MessageFactory.create_goodbye_message(self.id, topic))
        Logger.log(f'[CLIENT] REQ Socket Goodbye Sent')

        # Waits ACK
        # Blocking Call Intended
        req_proxy_socket.recv_pyobj()
        Logger.log(f'[CLIENT] REQ Socket ACK_Goodbye RECEIVED')

        req_proxy_socket.close()

        self.sub_socket.setsockopt_string(zmq.UNSUBSCRIBE, topic)

        Logger.log(f'[CLIENT] SUB Socket Unsubscribed topic: {topic}')

    def introduce_random_fault(self):
        time = random.randint(0, 9)

        if time > 0:
            Logger.info(f'Im sleeping for {time} seconds')
            self.discard_msgs = True
            sleep(time)

            Logger.success(f'Im back online')
            self.discard_msgs = False

    def subscribe_unsubscribe_random(self):

        random_int = random.randint(0, 10)

        # Probability of  3/10 of unsubscribe
        if random_int < 3:

            random_index = random.randint(0, len(self.topics) - 1)

            topic = self.topics[random_index]

            if topic in self.topics_unsubscribed_on_purpose:
                Logger.info(f'Topic Already Unsubscribed')
                return

            Logger.warning(f'Going to Unsubscribe {topic}')

            self.topics_unsubscribed_on_purpose.append(topic)

            self.unsubscribe(topic)
        else:

            if len(self.topics_unsubscribed_on_purpose) == 0:
                return

            topic_to_subscribe = self.topics_unsubscribed_on_purpose.pop()

            Logger.warning(f'Going to Subscribe Again {topic_to_subscribe}')

            self.subscribe(topic_to_subscribe)

    def run(self) -> None:
        Logger.success(f'ID: {self.id} | running')
        if self.error_spawner:
            set_interval(self.introduce_random_fault, 10, True)
            set_interval(self.subscribe_unsubscribe_random, 5, True)

        while True:
            self.get()


if __name__ == '__main__':
    topics = get_random_topics()

    if len(sys.argv) == 2:
        client = Client(int(sys.argv[1]), False, topics)
    elif len(sys.argv) == 3:
        if sys.argv[2] == 'true' or sys.argv[2] == 'True':
            client = Client(int(sys.argv[1]), True, topics)
        else:
            client = Client(int(sys.argv[1]), False, topics)
    else:
        client = Client(1, False, topics)

    client.run()
