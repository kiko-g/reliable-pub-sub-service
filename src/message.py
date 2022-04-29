from header import Header


class Message:
    def __init__(self, header: Header, body=None) -> None:
        self.header = header
        self.body = body
