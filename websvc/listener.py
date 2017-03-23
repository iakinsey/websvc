from gevent.wsgi import WSGIServer
from logging import info
from websvc.http import Request


class Listener:
    def __init__(self, service_manager, service_mapping, options):
        self.service_manager = service_manager
        self.service_mapping = service_mapping
        self.options = options

    def start(self):
        pass


class WebListener(Listener):
    url_mapping = None

    def start(self):
        self.url_mapping = {}
        self.map_services_to_urls()
        self.start_server()

    def map_services_to_urls(self):
        for name, service in self.service_mapping.items():
            self.map_service(name, service)

    def map_service(self, service_name, service):
        for attr_name in dir(service):
            attr = getattr(service, attr_name)

            if getattr(attr, "__public", None):
                method_name = attr.__name__
                url = "{}/{}".format(service_name, method_name)
                self.url_mapping[url] = attr

    def application(self, environ, start_response):
        request = Request(self.url_mapping, environ, start_response)

        return request.perform()

    def start_server(self):
        host = self.options["host"]
        port = self.options["port"]
        server = WSGIServer((host, port), self.application)

        info("Listening on http://{}:{}".format(host, port))
        server.serve_forever()
