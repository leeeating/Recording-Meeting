from pywinauto.application import Application
import urllib.parse
import logging
import os
import utils

logging.basicConfig(filename='daemon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s - %(message)s')
logger = logging.getLogger(__name__)


def hold_meeting(section):
    utils.maximize_windows_with_title_and_executable('Zoom', "Zoom.exe")
    pass

def join_meeting(room_id, password, name):
    # remove space in room_id
    room_id = room_id.replace(' ', '')

    os.system('taskkill /F /IM zoom.exe')
    utils.launch_cmd(rf'%appdata%\Zoom\bin\Zoom.exe "--url=zoommtg://zoom.us/join?action=join&confno={room_id}&pwd={password}&uname={urllib.parse.quote_plus(name)}"')

    try:
        zoom = Application(backend='uia').connect(title='Zoom', timeout=10)
        zoom.Zoom.type_keys('{ESC}')
    except:
        logger.error('Can not find zoom window after launching')

def terminate_meeting():
    try:
        zoom = Application(backend='uia').connect(title='Zoom', timeout=5)
        zoom.Zoom.type_keys('%{F4}')

        quit_dialog = Application(backend='uia').connect(title='結束會議或離開會議？', timeout=5)
        quit_btn = quit_dialog.結束會議或離開會議.child_window(title="離開會議", control_type="Button").wrapper_object()
        quit_btn.click_input()
    except Exception as e:
        logger.error(f'Error in termination of zoom: {e}')
    finally:
        os.system('TASKKILL /F /IM zoom.exe')