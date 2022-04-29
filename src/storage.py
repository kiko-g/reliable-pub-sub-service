import pickle
import os
from os import path

class Storage:
    def save(self,clients, messages):
        #confirms the existence of folder:
        if(path.exists("storage")==False):
            os.mkdir("storage")

        clients_file = open('storage/clients.pickle', 'wb')
        messages_file = open('storage/messages.pickle', 'wb')

        pickle.dump(clients, clients_file)
        pickle.dump(messages, messages_file)

        clients_file.close()  
        messages_file.close()


    def load(self):
        clients = {}
        messages = {}

        if(path.exists("storage")==False):
            os.mkdir("storage")
            
        clients_path='storage/clients.pickle'
        messages_path='storage/messages.pickle'

        if(path.exists(clients_path) and os.stat(clients_path).st_size != 0):
            clients_file = open(clients_path, 'rb')
            clients = pickle.load(clients_file)
            clients_file.close()  

        
        if(path.exists(messages_path) and os.stat(messages_path).st_size != 0):
            messages_file = open(messages_path, 'rb')
            messages = pickle.load(messages_file)
            messages_file.close()

        return clients, messages

