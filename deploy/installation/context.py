import os

from fabric.operations import sudo

import helpers
from singleton import Singleton


class Context(metaclass=Singleton):

    def __init__(self):
        self.proj_dir = None
        self.host = None
        self.os = None
        self.hostname = None
        self.is_node = None
        self.debug_mode = helpers.is_debug_mode()
        self.proj_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = f"{self.proj_dir}/templates"

    def get_hostname(self):
        self.hostname = sudo("hostname -s")
