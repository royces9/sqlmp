import importlib.util
import os

confdir = os.path.expanduser('~/.config/sqlmp/config.py')

spec = importlib.util.spec_from_file_location("config", confdir)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
