import configparser
import logging

logging.basicConfig(filename='reset.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
config.set('DEFAULT', 'state', 'idle')
config.set('DEFAULT', 'running', '')
with open('config.ini', 'w', encoding='utf-8') as configfile:
    config.write(configfile)

print('reset config.ini')
logging.info('reset config.ini')