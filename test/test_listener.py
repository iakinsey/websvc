from json import loads, dumps
from multiprocessing import Process
from os import kill
from urllib.request import urlopen
from websvc.listener import WebListener
from websvc.manager import ServiceManager
from websvc.service import Service, service, public


SERVICE_A_RESP = 1
SERVICE_B_RESP = 2

class ServiceA(Service):
    service_b = service("ServiceB")

    @public
    def call_b(self, arg):
        return self.service_b.get(arg)

    def get(self):
        return SERVICE_B_RESP


class ServiceB(Service):
    service_a = service("ServiceA")

    @public
    def call_a(self):
        return self.service_a.get()

    def get(self, arg):
        return arg


class TestListener:
    options = {
        "host": "localhost",
        "port": 54321
    }

    def run_server(self):
        services = [ServiceA, ServiceB]
        manager = ServiceManager(WebListener, services, self.options)

        manager.start()

    def test_service_call(self):
        url = "http://{host}:{port}".format(**self.options)
        url_a = "{}/{}/call_b".format(url, "ServiceA")
        url_b = "{}/{}/call_a".format(url, "ServiceB")
        process = Process(target=self.run_server)

        try:
            process.start()
            data = bytes(dumps({"arg": SERVICE_A_RESP}), encoding='utf-8')
            assert loads(urlopen(url_a, data).read())['data'] == SERVICE_A_RESP
            assert loads(urlopen(url_b).read())['data'] == SERVICE_B_RESP

            process.terminate()
        finally:
            if process.pid is not None:
                kill(process.pid, 9)
