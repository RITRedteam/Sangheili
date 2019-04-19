#import yaml
import os
import copy

# Read the config from the environment
config = copy.deepcopy(os.environ)

#with open("config.yml") as fil:
#    config = yaml.load(fil)
