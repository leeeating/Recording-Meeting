from pywinauto import application
from pywinauto.application import Application
from pywinauto import findwindows
from pywinauto.keyboard import send_keys
import pyautogui
import pyperclip
import time
import cv2
import ctypes
import os
import base64
import json

import utils
import logging


logging.basicConfig(filename='daemon.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s - %(message)s')
def join_meeting(room_id, name, email, password):
    utils.call_from_search('webex')

    time.sleep(10)
    img_join = cv2.imread('img/webex_join.png')
    x, y = pyautogui.locateCenterOnScreen(img_join, confidence=0.9)

    pyautogui.click(x, y)
    time.sleep(2)
    try:
        img_close_lobby = cv2.imread('img/webex_close_lobby.png')
        x, y, _, _ = pyautogui.locateOnScreen(img_close_lobby, confidence=0.9)
        x += 234
        y += 26
        pyautogui.click(x, y)
        time.sleep(2)
    except Exception as e:
        logging.error(e)

    pyperclip.copy(room_id)
    time.sleep(0.3)
    send_keys('^v{ENTER}')

    if password is not None:
        pyperclip.copy(password)
        time.sleep(5)
        send_keys('^v{ENTER}')
    
    # wait for prepare window popup
    time.sleep(5)
    # close mic warning and prompt
    send_keys('{ESC}{ESC}')
    time.sleep(1)

    # press enter to join
    send_keys('{ENTER}')

    # waiting for joining
    time.sleep(5)
    # maximize
    send_keys('{ESC}{LWIN down}{UP}{LWIN up}')
    print('open fin')

def join_meeting_uia(room_id, name, email, password):
    utils.call_from_search('webex')
    webex = Application(backend='uia').connect(title='Webex', timeout=100)

    try:
        back_btn = webex.Webex.child_window(title=" 返回", auto_id="MainWindowClass.OnboardingView.onboardingScreen.backButton", control_type="Button").wrapper_object()
        back_btn.click_input()
    except:
        pass

    # click join
    try:
        join_btn = webex.Webex.child_window(auto_id="MainWindowClass.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton", control_type="Button").wrapper_object()
        mode = 'NOLOGIN'
    except:
        try:
            join_btn = webex.Webex.child_window(auto_id="MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.expandedLine.joinMeetingLayoutWidget.joinMeetingButton", control_type="Button").wrapper_object()
            mode = 'LOGIN'
        except:
            print('join button not found')
            pass
    join_btn.click_input()
    time.sleep(1)

    if mode == 'NOLOGIN':
        room_id_textbox = webex.Webex.child_window(auto_id="MainWindowClass.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingGuestJoinWidget.meetingInfo.textInput", control_type="Edit").wrapper_object()
        room_id_textbox.set_text(room_id)

        name_textbox = webex.Webex.child_window(auto_id="MainWindowClass.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingGuestJoinWidget.displayName.textInput", control_type="Edit").wrapper_object()
        name_textbox.set_text(name)

        email_textbox = webex.Webex.child_window(auto_id="MainWindowClass.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingGuestJoinWidget.email.textInput", control_type="Edit").wrapper_object()
        email_textbox.set_text(email)

        next_button = webex.Webex.child_window(title=" 下一步", auto_id="MainWindowClass.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingGuestJoinWidget.nextButton", control_type="Button").wrapper_object()
        next_button.click_input()
    else:
        pyperclip.copy(room_id)
        send_keys('^v{ENTER}')
        if password is not None:
            print('webex password available')
            time.sleep(5)
            pyperclip.copy(password)
            send_keys('^v{ENTER}')
        
    
    time.sleep(10)


    """ update cause error,  original atmgr.exe is the main window of meeting, now main windows can't found
    # prepare window
    meeting_window_pid = application.process_from_module(module='atmgr.exe')
    webex_meeting_window = Application(backend='uia').connect(process=meeting_window_pid, timeout=20)
    time.sleep(3)



    # webex_meeting_window.Pane.print_control_identifiers()
    # waiting for prepare window constructs
    try:
        join_meeting_button = webex_meeting_window.Pane.Button7.wrapper_object()
        # join_meeting_button = webex_meeting_window.Pane.child_window(title="加入會議").wrapper_object()
        join_meeting_button.click_input()
    except Exception as e:
        print(e)
        pass
    """

    
    # close mic warning and prompt
    send_keys('{ESC}{ESC}')
    time.sleep(1)

    # press enter to join
    send_keys('{ENTER}')

    # waiting for joining
    time.sleep(3)
    
    """ agmtr.exe missing
    # maximize
    window = findwindows.find_windows(process=meeting_window_pid)[0]
    webex_meeting_window.window_(handle=window).set_focus()
    ctypes.windll.user32.ShowWindow(window, 3)
    """

    # maximize
    send_keys('{ESC}{LWIN down}{UP}{LWIN up}')
    print('open fin')

def join_meeting_url(room_id):
    # terminate old window
    # terminate_meeting_taskkill()
    time.sleep(2)

    jt_json = {
        "t": 36,
        "t1": round(time.time() * 1000),
        "up": 3
    }
    jt_str = json.dumps(jt_json)
    jt_base64 = base64.b64encode(jt_str.encode('UTF-8'))
    room_id = room_id.replace(' ', '')

    url = f'webex://meet?jt={jt_base64.decode()}=&sip={room_id}@meet359.webex.com&mtid=&vp=&dns=meet359.webex.com&flag=33&siteurl=meet359&rc=4&en=prod&bv=118&bt=12'
    utils.launch_cmd(f'cmd /C start "" "{url}"')

    time.sleep(5)
    send_keys('{ESC}{ESC}')
    time.sleep(1)
    send_keys('{ENTER}')

def terminate_meeting():
    terminate_meeting_taskkill()

def terminate_meeting_keyboard():
    pass

def terminate_meeting_taskkill():
    os.system('taskkill /F /IM CiscoCollabHost.exe')

def terminate_meeting_uia():
    meeting_window_pid = application.process_from_module(module='atmgr.exe')
    webex_meeting_window = Application(backend='uia').connect(process=meeting_window_pid, timeout=20)

    window = findwindows.find_windows(process=meeting_window_pid)[0]
    ctypes.windll.user32.SetForegroundWindow(window)

    time.sleep(0.5)
    webex_meeting_window.Pane.type_keys('{ESC}{ENTER}')
    # webex_meeting_window.Pane.type_keys('{LWIN down}{DOWN}{LWIN up}')

if __name__ == '__main__':
    # join_meeting_uia('2644 400 7600', 'bar', 'example@example.com')
    join_meeting_url('2641 033 9603')
    time.sleep(20)
    print('close')
    # terminate_meeting_uia()