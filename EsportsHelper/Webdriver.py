import os
import socket
import shutil
import requests
import urllib3
from requests import Response

import undetected_chromedriver as uc
from rich import print
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import HttpClient

from EsportsHelper.Config import config
from EsportsHelper.Logger import log
from EsportsHelper.I18n import i18n
from EsportsHelper.Stats import stats

_ = i18n.getText
_log = i18n.getLog
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CustomHttpClient(HttpClient):
    def get(self, url, params=None) -> Response:
        proxies = {}
        if config.proxy.startswith('http'):
            proxies={'http': config.proxy,
                     'https': config.proxy
            }
        return requests.get(url, params, proxies=proxies, verify=False)


def checkPort(ip, port):
    """
    Check if the port is occupied
    """
    s = socket.socket()
    try:
        s.connect((ip, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def getDriverVersion(chromeDriverManager):
    """
    Get the version number of the ChromeDriver being used by the driver instance.

    Args:
        chromeDriverManager (ChromeDriverManager): An instance of the ChromeDriverManager class.

    Returns:
        int: The version number of the ChromeDriver being used by the driver instance,
         or a default version of 108 if it is unable to retrieve the version number.
    """
    try:
        version = int(chromeDriverManager.driver.get_latest_release_version().split(".")[0])
    except Exception:
        version = 108
    return version


def addWebdriverOptions(options, version):
    """
    Adds options to a Chrome webdriver instance.

    Args:
    - options: An instance of ChromeOptions to which the options will be added.

    Returns:
    - An instance of ChromeOptions with the added options.

    Raises:
    - None
    """
    if checkPort("localhost", 9222):
        log.info(_log("检测到端口9222被占用"))
        if checkPort("localhost", 9229):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("localhost", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            sock.close()
            log.error(_log("检测到端口9229被占用,将使用随机端口:" + str(port)))
            if config.headless:
                stats.info.append(_("检测到端口9222和9229都被占用,将使用随机端口:", color="yellow")
                                  + f"[yellow]{port}[/yellow]")
                stats.info.append(_("如需使用方案一,请在打开的网页中的Configure选项中配置以下信息:", color="yellow"))
                stats.info.append("localhost:" + str(port))

            stats.debugPort = port
        else:
            stats.debugPort = 9229
            log.info(_log("使用默认端口9229"))
    else:
        stats.debugPort = 9222
        log.info(_log("使用默认端口9222"))
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-audio-output')
    options.add_argument('--autoplay-policy=no-user-gesture-required')
    options.add_argument("--disable-gpu")
    options.add_argument('--enable-features=WebContentsForceDark')
    options.add_argument("--disable-dev-shm-usage")
    options.debugger_address = "127.0.0.1:" + str(stats.debugPort)
    options.set_capability("goog:loggingPrefs", {
        'performance': 'ALL'
    })
    options.set_capability("goog:perfLoggingPrefs", {
        'enableNetwork': True,
        'enablePage': False,
        'enableTimeline': False
    })

    prefs = {
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False,
    }
    options.add_experimental_option('prefs', prefs)
    if config.proxy:
        options.add_argument(f"--proxy-server={config.proxy}")
    if config.headless and not config.isDockerized:
        options.add_argument("--headless=new")

        windowsAgent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"
        macAgent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"
        linuxAgent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"

        if config.platForm == "windows":
            userAgent = windowsAgent
        elif config.platForm == "mac":
            userAgent = macAgent
        elif config.platForm == "linux":
            userAgent = linuxAgent
        else:
            # Default to one agent, just in case
            userAgent = windowsAgent

        options.add_argument(f'user-agent={userAgent}')
    return options


def createWebdriver():
    """
    Creates a webdriver instance of uc.Chrome with specified options and configurations.

    Returns:
        A uc.Chrome instance.
    """
    customPath = ".\\driver"
    if os.path.exists(customPath):
        shutil.rmtree(customPath)
    http_client = CustomHttpClient()
    download_manager = WDMDownloadManager(http_client)
    chromeDriverManager = ChromeDriverManager(cache_manager=DriverCacheManager(customPath), download_manager=download_manager)
    if config.isDockerized:
        driverPath = "/undetected_chromedriver/chromedriver"
    else:
        if config.platForm in ["linux", "mac"]:
            if config.arm64:
                username = os.getlogin()
                driverPath = f"/home/{username}/.local/share/undetected_chromedriver/chromedriver"
                if not os.path.exists(driverPath):
                    log.error(_log("找不到 chromedriver"))
                    return
            else:
                customPath = "driver"
                if os.path.exists(customPath):
                    shutil.rmtree(customPath)
                chromeDriverManager = ChromeDriverManager(cache_manager=DriverCacheManager(customPath), download_manager=download_manager)
                driverPath = chromeDriverManager.install()
        elif config.platForm == "windows":
            driverPath = chromeDriverManager.install()
        else:
            log.error(_("不支持的操作系统"))

    print(_("正在准备中...", color="yellow"))
    log.info(_log("正在准备中..."))
    version = getDriverVersion(chromeDriverManager)
    log.info(_log("取得版本..."))
    options = addWebdriverOptions(uc.ChromeOptions(), version)
    log.info(_log("取得選項..."))

    kwargs = {
        "options": options,
        "driver_executable_path": driverPath,
        "version_main": version,
        "browser_executable_path": config.chromePath if config.chromePath else None,
        "user_data_dir": config.userDataDir if config.userDataDir else None,
    }
    log.info(_log("正在创建浏览器实例..."))
    return uc.Chrome(**{k: v for k, v in kwargs.items() if v})


class Webdriver:
    def __init__(self) -> None:
        pass
