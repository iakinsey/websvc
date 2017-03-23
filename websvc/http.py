from gevent.monkey import patch_all


patch_all()


from cgi import FieldStorage
from json import dumps, loads
from json.decoder import JSONDecodeError
from sys import argv
from traceback import print_exc
from gevent.wsgi import WSGIServer
from os import mkdir, listdir
from urllib.parse import parse_qs


OPTIONS = """Usage:
  run [host] [port]"""


class RequestFailure(Exception):
    pass


class Request:
    encoding = "utf-8"
    code_map = {
        200: "200 OK",
        400: "400 Bad Request",
        404: "404 Not Found",
        405: "405 Method not allowed",
        500: "500 Internal Server Error"
    }

    def __init__(self, url_mapping, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.url_mapping = url_mapping
        self.response = {'success': False}
        self.code = None
        self.method = self.environ['REQUEST_METHOD']
        self.headers = [
            ('Content-Type', 'text/plain; charset={}'.format(self.encoding)),
            ('Access-Control-Allow-Origin', '*')
        ]

    def get_arguments(self):
        try:
            length = int(self.environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            length = 0

        if length == 0:
            return {}

        body = environ['wsgi.input'].read(length)

        try:
            # TODO check argument spec
            return json.loads(body)
        except JSONDecodeError:
            # TODO change this exception to something more appropriate.
            raise ValueError()

    def perform(self):
        try:
            path = self.environ['PATH_INFO'].strip('/')
            fn = self.url_mapping.get(path)
            arguments = self.get_arguments()

            if not fn:
                self.code = 404
            else:
                self.response['data'] = fn(**arguments)
                self.response['success'] = True
                self.code = 200
        except RequestFailure as e:
            self.response['error'], self.code = e.args
        except:
            print_exc()
            self.code = 500
        finally:
            return self.respond()

    def respond(self):
        if self.code is None:
            if self.response['success']:
                self.code = 200
            else:
                self.code = 500

        formal_code = self.code_map[self.code]
        self.response['http'] = self.code
        self.start_response(formal_code, self.headers)

        json_data = dumps(self.response)
        payload = bytes(json_data, encoding=self.encoding)
        self.headers.append(("Content-Length", len(payload)))

        return [payload]

    def fail(self, reason, code=400):
        raise RequestFailure(reason, code)
