from websvc.service import service as service_pointer


class ServiceManager:
    listner = None

    def __init__(self, Listener, services, options=None):
        self.Listener = Listener
        self._services = services
        self._service_mapping = {}
        self.options = options
        self.add_services()

    def add_services(self):
        for service in self._services:
            self.register_service(service)

        for service_name, service in self._service_mapping.items():
            for attr_name in dir(service):
                attr = getattr(service, attr_name)

                if type(attr) is service_pointer:
                    dependency = self._service_mapping[attr.name]
                    setattr(service, attr_name, dependency)

    def register_service(self, Service):
        self._service_mapping[Service.__name__] = Service(self)

    def start(self):
        for service in self._service_mapping.values():
            service.on_start()

        self.start_listener()

    def start_listener(self):
        self.listener = self.Listener(self, self._service_mapping, self.options)
        self.listener.start()
