from cgi import FieldStorage
from functools import wraps
from gevent.wsgi import WSGIServer
from inspect import getargspec
from json import dumps, loads
from json.decoder import JSONDecodeError
from os import mkdir, listdir
from sys import argv
from traceback import print_exc
from websvc.error import ServiceError
from urllib.parse import parse_qs


OPTIONS = """Usage:
  run [host] [port]"""


def validate_arguments(fn):
    argspec = getargspec(fn)
    desired_args = argspec.args

    if argspec.defaults:
        desired_args = argspec.args[:-len(argspec.defaults)]

    desired_args = set(desired_args[1:])

    @wraps(fn)
    def func(arguments):
        difference = desired_args.difference(arguments)

        if difference:
            raise ValueError("Missing keys: {}".format(difference))

        return fn(**arguments)

    return func

def wrap_url_mapping(url_mapping):
    return {url: validate_arguments(fn) for url, fn in url_mapping.items()}


class Request:
    encoding = "utf-8"
    code_map = {
        200: "200 OK",
        204: "204 No Content",
        400: "400 Bad Request",
        404: "404 Not Found",
        405: "405 Method not allowed",
        500: "500 Internal Server Error"
    }

    force_allow_headers = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Credentials', 'true'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ('Access-Control-Max-Age', 1728000),
        ('Content-Type', 'text/plain charset=UTF-8'),
        ('Content-Length', 0)
    ]

    def __init__(self, url_mapping, options, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.url_mapping = wrap_url_mapping(url_mapping)
        self.response = {'success': False}
        self.code = None
        self.options = options
        self.debug = self.options.get('debug')
        self.method = self.environ['REQUEST_METHOD']
        self.indicate_allow_all = self.debug and self.method == 'OPTIONS'
        self.headers = [
            ('Content-Type', 'text/plain; charset={}'.format(self.encoding)),
        ]

    def get_arguments(self):
        try:
            length = int(self.environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            length = 0

        if length == 0:
            return {}

        body = self.environ['wsgi.input'].read(length)

        try:
            return loads(body)
        except JSONDecodeError:
            # TODO change this exception to something more appropriate.
            raise ValueError()

    def perform(self):
        self.code = 200

        try:
            if self.indicate_allow_all:
                self.code = 204
                self.headers.extend(self.force_allow_headers)
            else:
                path = self.environ['PATH_INFO'].strip('/')
                fn = self.url_mapping.get(path)
                arguments = self.get_arguments()

                if not fn:
                    self.code = 404
                else:
                    self.response['data'] = fn(arguments)
                    self.response['success'] = True
        except ServiceError as e:
            self.response['error'] = e.args[0]
            self.response['code'] = e.code
            self.code = 400
        except:
            print_exc()
            self.code = 500
            self.response['error'] = "Internal server error"
            self.response['code'] = 0
        finally:
            return self.respond()

    def respond(self):
        formal_code = self.code_map[self.code]
        self.response['http'] = self.code
        self.start_response(formal_code, self.headers)

        if self.indicate_allow_all:
            payload = ''
        else:
            json_data = dumps(self.response)
            payload = bytes(json_data, encoding=self.encoding)

        self.headers.append(("Content-Length", len(payload)))

        return [payload]
