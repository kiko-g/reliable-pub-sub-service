import hashlib
import sys
import time
import zmq
from logger import Logger
from utils import get_topics

context = zmq.Context()


class Server:
    def __init__(self, server_id: int, xsub_port: int = 5556) -> None:
        self.topics = get_topics()
        self.id = hashlib.md5(str(server_id).encode()).hexdigest()
        self.xsub_address = f'tcp://127.0.0.1:{xsub_port}'
        self.pub_socket = context.socket(zmq.PUB)
        self.pub_socket.connect(self.xsub_address)

    def __str__(self):
        return 'Server ' + str(self.id)

    def put(self, topic, message) -> None:

        raw_message = [
            topic.encode('utf-8'),
            hashlib.md5(f'{topic}{message}{time.time()}'.encode()).hexdigest().encode('utf-8'),
            message.encode('utf-8'),
        ]
        self.pub_socket.send_multipart(raw_message)

        Logger.info(f'[Server] Pub Socket send: {raw_message}')

    def run(self) -> None:
        Logger.success(f'{self} running')
        while True:
            topic = input('Input topic: ')
            message = input('Input message for topic %r: ' % topic)

            if topic not in self.topics:
                self.topics.append(topic)

            self.put(topic, message)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        server = Server(int(sys.argv[1]))
    else:
        server = Server(1)

    server.run()
