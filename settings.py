import configparser

config = configparser.ConfigParser()
config.read('.env')

general_env = config["General"]

API_TOKEN = general_env['API_TOKEN']
