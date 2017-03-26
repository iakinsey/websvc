from importlib import import_module
from os import listdir
from websvc.service import Service


def get_services(module_base, path):
    services = []
    files = [i.replace(".py", "") for i in listdir(path) if i != "__init__.py"]

    for file_name in files:
        module_name = "{}.{}".format(module_base, file_name)
        module = import_module(module_name)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if not isinstance(attr, type) or attr == Service:
                continue

            if issubclass(attr, Service):
                services.append(attr)

    return services
