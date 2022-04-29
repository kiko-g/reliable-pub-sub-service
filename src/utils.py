import os
from copy import copy
from pathlib import Path
from random import sample, randrange
from threading import Timer


def list_clients_existent_at_give_time_for_give_topic(topic: str, clients: dict) -> list:
    list_to_return = []
    topic = topic

    if topic not in clients:
        return []

    for key in clients[topic]:
        list_to_return.append(copy(clients[topic][key].client_id))

    return list_to_return


def set_interval(action, interval=3, first_time=False, active=True):
    if not first_time:
        action()

    if active:
        Timer(
            interval,
            set_interval,
            kwargs={'action': action, 'interval': interval, 'active': active}
        ).start()


def get_topics():
    path = Path(os.getcwd())

    suffix = ""

    if "src" in str(path.parent.absolute()):
        suffix = "/resources/topics.txt"
    else:
        suffix = "/src/resources/topics.txt"

    with open(f"{path.parent.absolute()}{suffix}", "r") as f:
        return f.read().splitlines()


def get_random_topics():
    topics = get_topics()
    amount = randrange(0, len(topics)) + 1
    return sample(topics, amount)
