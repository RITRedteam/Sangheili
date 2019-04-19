#import yaml
import os
import copy

# Read the config from the environment
config = copy.deepcopy(os.environ)
#config['reserve_addresses'] = os.environ.get("reserve_addresses", 'false').lower().strip() in ["true", "yes", "1", "t"]
#config['validate_addresses'] = os.environ.get("validate_addresses", 'false').lower().strip() in ["true", "yes", "1", "t"]
try:
    config['address_count'] = int(os.environ.get("address_count", "30"))
except:
    config['address_count'] = 30
#with open("config.yml") as fil:
#    config = yaml.load(fil)
