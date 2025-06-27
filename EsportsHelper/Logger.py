import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from rich import print

# 延遲 import config 以避免循環引用

FILE_SIZE = 1024 * 1024 * 100
BACKUP_COUNT = 5
PROGRAM_NAME = "EsportsHelper"
GITHUB_ADDRESS = "https://github.com/Yudaotor/EsportsHelper"
VERSION = "2.5.0"


class Logger:
    @staticmethod
    def createLogger(log_path=Path("./logs/programs")):
        """
        Create and return a logger instance
        Args:
            log_path (Path, optional): The path where the log file is saved. Defaults to Path("./logs/programs").
        Returns:
            logging.Logger: Logger instance.
        """
        log_path.mkdir(parents=True, exist_ok=True)
        Path("./logs/pics").mkdir(parents=True, exist_ok=True)
        Path("./dropsHistory").mkdir(parents=True, exist_ok=True)
        with open(f'./dropsHistory/{time.strftime("%Y%m%d-")}drops.txt', "a+", encoding="utf-8"):
            pass
        level = logging.INFO
        fileHandler = RotatingFileHandler(
            log_path / f"{PROGRAM_NAME}V{VERSION}_{time.strftime('%m.%d_%H-%M')}.log",
            mode="a+",
            maxBytes=FILE_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )

        logging.basicConfig(
            format="%(asctime)s %(levelname)s: %(message)s",
            level=level,
            handlers=[fileHandler],
        )
        logg = logging.getLogger(PROGRAM_NAME)
        logg.info("-" * 71)
        logg.info(f"{'-' * 22} Program started {VERSION}   {'-' * 23}")
        logg.info(f"{'-' * 22} Open Source on github  {'-' * 22}")
        logg.info(f"{'-' * 7} Address: {GITHUB_ADDRESS} {'-' * 6}")
        logg.info(f"{'-' * 16} Please give me a star,Thanks(*^_^*)  {'-' * 15}")
        logg.info("-" * 71)
        return logg


class LoggerWrapper:
    def __init__(self, logger):
        self._logger = logger

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)
        try:
            from EsportsHelper.Config import config
            if getattr(config, "isDockerized", False):
                print(msg)
        except Exception:
            pass

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)
        try:
            from EsportsHelper.Config import config
            if getattr(config, "isDockerized", False):
                print(f"[red]{msg}[/red]")
        except Exception:
            pass

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)
        try:
            from EsportsHelper.Config import config
            if getattr(config, "isDockerized", False):
                print(f"[yellow]{msg}[/yellow]")
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._logger, name)

log = LoggerWrapper(Logger().createLogger())


def delimiterLine(color="bold yellow"):
    """
    Print delimiter line
    """
    print(
        f"[{color}]>_<"
        f"{'=' * 27}"
        f">_<"
        f"{'=' * 27}"
        f">_<[/{color}]"
    )
