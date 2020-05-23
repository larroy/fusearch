import yaml
import os

# FIXME lockfile
class Config(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_file(conf_file):
        assert os.path.isfile(conf_file)
        with open(conf_file, "r") as fd:
            cfg = yaml.safe_load(fd.read())
        if cfg:
            return Config(**cfg)
        return Config()

    def __str__(self):
        return self.__class__.__name__ + "(" + str(self.__dict__) + ")"
