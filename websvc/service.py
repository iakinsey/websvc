class service:
    def __init__(self, name):
        self.name = name


class Service:
    def __init__(self, manager):
        self.__manager = manager

    def on_start(self):
        pass


def public(fn):
    fn.__public = True

    return fn
