from obswebsocket import obsws, requests
import configparser
import logging

import os

import time

import webex_actions as webex
import zoom_actions as zoom
import utils

logging.basicConfig(filename='daemon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s - %(message)s')

logger = logging.getLogger(__name__)

client = None

def init():
    logger.info('Init obs socket')
    obs_config = configparser.ConfigParser()
    obs_config.read('obs_config.ini', encoding='utf-8')
    host = obs_config['DEFAULT']['host']
    port = obs_config['DEFAULT']['port']
    logger.info(f'Connecting to obs websocket {host}:{port}')
    password = obs_config['DEFAULT']['password']

    global client
    client = obsws(host, port, password)
    client.connect()

def init_obs():
    if client is None:
        try:
            init()
        except:
            logger.warning('OBS maybe not running, try to launch OBS')
            # utils.launch_cmd(r'"C:\Program Files\obs-studio\bin\64bit\obs64.exe\"')
            try:
                utils.call_from_search('obs')
            except Exception as e:
                logger.error('Failed to launch obs from search')
                logger.error(e)
            time.sleep(10)
            try:
                init()
            except:
                logger.error('OBS launching retry failed')
                return False

def destroy():
    global client
    if client is None:
        return
    client.disconnect()

def start_recording(entry, config):
    init_obs()

    if entry['type'] == 'webex':
        logger.info('Launching webex')
        try:
            room_id = entry['room']
            name = entry['name']
            email = entry['email']
            password = entry.get('password', None)

            logger.info(f'Room id: {room_id}, Name: {name}, Email: {email}, Password: {password}')
            webex.join_meeting(room_id, name, email, password)
        except Exception as e:
            logger.error(e)
            print(e)
            return False
        logger.info('Webex started')

    elif entry['type'] == 'zoom':
        logger.info('Launching zoom')
        try:
            room_id = entry['room']
            password = entry['password']
            name = entry['name']
            
            logger.info(f'Room id: {room_id}, Password: {password}, Name: {name}')
            zoom.join_meeting(room_id, password, name)

        except Exception as e:
            logger.log('Zoom is failed to start')
            logger.error(e)
            print(e)
            return False
        logger.info('Zoom started')

    # switch scene
    scene_name = entry.get('scene', config['SCENES'][entry['type']])
    try:
        client.call(requests.SetCurrentProgramScene(sceneName=scene_name))
    except Exception as e:
        logger.error(f'Can not switch to scene {scene_name}')
        logger.error(e)
        print(f'Can not switch to scene {scene_name}')
        return False

    print('start recording', entry)
    logger.info('Start recording')
    try:
        client.call(requests.StartRecord())
    except Exception as e:
        logger.error('Can not start recording')
        logger.error(e)
        print(e)
        return False
    return True

def maintain(section):
    if section['type'] == 'zoom':
        zoom.hold_meeting(section)
    pass

def stop_recording(entry):
    if client is None:
        try:
            init()
        except:
            logger.error('Can not connect to OBS when stop recording')

    
    print('stop recording', entry)
    logger.info('Stop recording')
    obs_fail_flag = False
    try:
        res = client.call(requests.StopRecord())
    except Exception as e:
        logger.error('OBS call StopRecord failed')
        logger.error(e)
        obs_fail_flag = True
    
    if entry['type'] == 'webex':
        # terminate webex
        webex.terminate_meeting()
    elif entry['type'] == 'zoom':
        # terminate Zoom
        zoom.terminate_meeting()

    # save OBS output
    if not obs_fail_flag and len(res.datain) == 0:
        logger.warning('No outputPath in the response, recording maybe failed')
        return False
    elif not obs_fail_flag:
        file_path = res.datain['outputPath']
        filename = os.path.basename(file_path)
        new_filename = entry['filename'].format(filename)
        new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
        time.sleep(10)  # wait for obs release the file
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            logger.error(e)
            logger.error(f'Can not rename the recording file, keep the original name {file_path}')
        logger.info(f'Save the recording file to path: {file_path}')
        return True
    else:
        return False

if __name__ == "__main__":
    init()