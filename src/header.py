import time


class Header:

    def __init__(self, msg_type: str):
        self.msg_type = msg_type
        self.address_origin = None
        self.id_origin = None
        self.topic = None
        self.timestamp = time.time()
        self.message_id = None
