import configparser
import datetime
import logging
import isodate

import actions

logging.basicConfig(filename='daemon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s - %(message)s')

# get logger
logger = logging.getLogger(__name__)

logger.info('=== Round started ===')

# read config.ini
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

schedule_config = configparser.ConfigParser()
schedule_config.read('schedule.ini', encoding='utf-8')

# global settings
state = config['DEFAULT']['state']
running = config['DEFAULT']['running']
remove_expired = config['DEFAULT'].getboolean('remove_expired')

# mark the expired entry to remove
entry_to_remove = []


for entry in schedule_config:
    # skip not meeting section
    if entry == 'DEFAULT':
        continue
    try:
        section = schedule_config[entry]
        logger.info(f'Checking entry [{entry}]')
        start = section['start']
        start_date = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end = section['end']
        end_date = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        keep = schedule_config.get(entry, 'keep')

        # check start < end
        if start_date > end_date:
            logger.warning(f'Start date is after end date in section [{entry}]')
            print('start date is after end date', entry)
            continue

        # if end is in the past, and running is current entry, stop the section
        if end_date < datetime.datetime.now() and running == entry:
            logger.info(f'Stop task [{entry}]')
            print('stop task', entry)
            actions.stop_recording(section)
            config.set('DEFAULT', 'running', '')
            config.set('DEFAULT', 'state', 'idle')

            # if keep type is repeat, add time to start and end time
            if keep == 'repeat':
                repeat_duration = schedule_config.get(entry, 'repeat') # fallback is delta 0 present in PT
                repeat_delta = isodate.parse_duration(repeat_duration)
                logger.info(f'Section [{entry}] repeatting add {repeat_delta}')
                new_start_date = start_date + repeat_delta
                new_end_date = end_date + repeat_delta
                schedule_config.set(entry, 'start', new_start_date.strftime('%Y-%m-%d %H:%M:%S'))
                schedule_config.set(entry, 'end', new_end_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        # if start date is in the past, and end date is in the future(now in the section)
        elif start_date < datetime.datetime.now() and end_date > datetime.datetime.now():
            # if state is idle, start the section
            if state == 'idle':
                logger.info(f'Start task [{entry}]')
                print('start task', entry)
                actions.start_recording(section, config)
                config.set('DEFAULT', 'running', entry)
                config.set('DEFAULT', 'state', 'running')
                continue
            elif not running == entry:
                print(f'Time overlap [{entry}]')
                logger.warning(f'Time overlap appears in section recording section [{running}] and idle seciton [{entry}]')
                continue
            elif running == entry:
                # session running, maintain
                actions.maintain(section)
        else:
            logger.info(f'No action to [{entry}]')
        if remove_expired and end_date < datetime.datetime.now() and keep == 'false':
            logger.info(f'Entry [{entry}] expired')
            entry_to_remove.append(entry)
    except KeyError as e:
        logger.warning(f'Key {e} missing in config in section {entry}]')
        continue

logger.info('Removing expired entries...')
for entry in entry_to_remove:
    logger.info(f'Removing entry [{entry}]')
    schedule_config.remove_section(entry)

logger.info('Saving config...')
with open('config.ini', 'w', encoding='utf-8') as configfile:
    config.write(configfile)

logger.info('Saving schedule...')
with open('schedule.ini', 'w', encoding='utf-8') as configfile:
    schedule_config.write(configfile)

logger.info('=== Round finished ===')