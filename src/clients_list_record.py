class ClientListRecord:
    def __init__(self, client_id: str, client_address: str, timestamp_join: int):
        self.client_id = client_id
        self.client_address = client_address
        self.timestamp_join = timestamp_join
