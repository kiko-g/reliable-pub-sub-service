from header import Header
from message import Message


class MessageFactory:
    # Messages

    @staticmethod
    def create_hello_message(id_origin: str, address_origin: str, topic: str):
        header = Header("hello")
        header.id_origin = id_origin
        header.address_origin = address_origin
        header.topic = topic

        return Message(header)

    @staticmethod
    def create_goodbye_message(id_origin: str, topic: str):
        header = Header("goodbye")
        header.id_origin = id_origin
        header.topic = topic

        return Message(header)

    @staticmethod
    def create_topic_message(topic: bytes, message_id: bytes, body: bytes):
        header = Header("data")
        header.topic = topic.decode()
        header.message_id = message_id.decode()

        return Message(header, body.decode())

    # Replies

    @staticmethod
    def create_ack_welcome_reply():
        return Message(Header("ack_welcome"))

    @staticmethod
    def create_ack_goodbye_reply():
        return Message(Header("ack_goodbye"))

    @staticmethod
    def create_ack_received_reply(id_origin: str, message_id: bytes, topic: bytes):
        header = Header("ack_received")
        header.id_origin = id_origin
        header.message_id = message_id.decode()
        header.topic = topic.decode()
        return Message(header)

    @staticmethod
    def create_ack_received_reply_after_retransmission(id_origin: str, message_id: str, topic: str):
        header = Header("ack_received")
        header.id_origin = id_origin
        header.message_id = message_id
        header.topic = topic
        return Message(header)

    @staticmethod
    def create_retransmission_message(topic: str, message_id: str, body: str):
        header = Header("retransmit")
        header.topic = topic
        header.message_id = message_id

        return Message(header, body)

    @staticmethod
    def create_dummy_ok_msg():
        header = Header("ok")
        return Message(header)
