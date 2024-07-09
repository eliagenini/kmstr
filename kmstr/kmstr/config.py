__author__ = 'eliagenini'

import yaml

with open('config.yaml') as config:
    cfg = yaml.load(config, Loader=yaml.FullLoader)
