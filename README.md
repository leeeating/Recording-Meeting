# Recording-Meeting

- [Introduciton](#introduciton)
- [Prerequisite](#prerequisite)
- [Getting Started](#getting-started)
  - [下載程式](#下載程式)
  - [開始使用](#開始使用)
- [Configuration](#configuration)
  - [Email Configuration for sender](#email-configuration-for-sender)
  - [Webex Points Configuration](#webex-points-configuration)
  - [Application Path Configuration](#application-path-configuration)

## Introduciton

此專案為線上會議自動錄製軟體，會議軟體限制為`Webex`, `Zoom` ，使用**PyQt6**開發桌面應用及**FastApi**後端。


## Getting Started

### 下載程式

此專案要部屬到小四以外的電腦可以使用`Installation.bat`。
在其他電腦上雙點擊`Installation.bat`，即可快速下載，預設下載到Documents資料夾中。

### 開始使用

在檔案總管中開啟本專案的資料夾，找到Script子資料夾中的`使用者介面-會議記錄.bat`, `後端伺服器-會議記錄.bat`，為這兩個檔案在桌面建立捷徑，方便以後使用。

1. 先設定 Configuration
2. 雙點擊執行`後端伺服器-會議記錄.bat`，開啟後端。
3. 雙點擊執行`使用者介面-會議記錄.bat`，開使安排錄影。

p.s.: 在後端沒有被關閉的情況下，只需要執行 第三步

## Configuration

### Email Configuration for sender

此專案需要自動寄送 Gmail，因此需要事先設定**寄件者**的 Gmail 帳號及密碼，才能使用程式自動寄送

設定步驟如下

1. 進入帳號管理頁面
   ![alt text](readme_figure/account_manager.png)

2. 搜尋`應用程式密碼`
   ![alt text](readme_figure/search.png)

3. 設定並紀錄`應用程式密碼`，名字可以隨便取，<mark>產生的密碼要保存</mark>。

   ![alt text](readme_figure/setting.png)

4. 寫入`.env`檔

   在.env中找到對應的變數更改數值

   ```ini
   DEFAULT_USER_EMAIL="account@gmail.com"
   EMAIL_APP_PASSWORD="password"
   ```

### Webex Points Configuration

在 webex 模式中需要設定滑鼠點擊位置，在其他電腦設定時需要下載[**Accessibility Insights For Windows**](https://accessibilityinsights.io/downloads/)。

先隨便開啟一個會議，將整個視窗最大化後，再將滑鼠游標移到三個不同的 Layout 上，紀錄程式中顯示的座標(直接複製貼上原始字串，不用額外處理)。
最後貼到`.env`檔中對應的變數中(`WEBEX_GRID_POINT`, `WEBEX_STACKED_POINT`, `WEBEX_SIDE_BY_SIDE_POINT`)。

p.s.: 滑鼠移動到元件上面，需要顯示藍色外框才算偵測成功

![alt text](readme_figure/points_setting.png)

### Application Path Configuration

1.  需要找出`webex`, `zoom`, `obs`的執行路徑，以及OBS中的場景設定名稱

    進入.env設定 　`WEBEX_APP_PATH`, `ZOOM_APP_PATH`, `OBS_PATH`

    可以先在電腦上確認以下路徑是否有該Application

    p.s.: `<user name>`為變數，每台電腦的設定都不一樣

    ```ini
    OBS_PATH="C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    WEBEX_APP_PATH="C:\Users\<user name>\AppData\Local\CiscoSparkLauncher\CiscoCollabHost.exe"
    ZOOM_APP_PATH="C:\Users\<user name>\AppData\Roaming\Zoom\bin\Zoom.exe"
    ```

    <details>
    <summary>如何使用指令找出路徑</summary>
    程式要遞迴搜尋需要等一下

    ```powershell
    Get-ChildItem -Path $env:LOCALAPPDATA, $env:APPDATA -Filter "Zoom.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName

    Get-ChildItem -Path $env:LOCALAPPDATA, $env:ProgramFiles -Filter "Webex.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName

    Get-ChildItem -Path $env:LOCALAPPDATA, $env:ProgramFiles -Filter "obs64.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
    ```

    </details>

<br>

2.  開啟OBS設定針對Zoom或是Webex的場景，名字可以隨便取或是沿用原本的設定，只需要跟`.env`中一樣就好。

    ![alt text](readme_figure/obs_scene.png)

    ```ini
    WEBEX_SCENE_NAME="WEBEX_APP"
    ZOOM_SCENE_NAME="ZOOM_APP"
    ```
