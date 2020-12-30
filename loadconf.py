import importlib.util
import os
import sys

confdir = os.path.expanduser('./config.py')
module_name = "config"

spec = importlib.util.spec_from_file_location(module_name, confdir)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)
