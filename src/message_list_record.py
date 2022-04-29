from message import Message


class MessageListRecord:
    def __init__(self, message: Message, clients_unacked: list):
        self.message = message
        self.clients_unacked = clients_unacked
