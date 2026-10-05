import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QObject, Slot, Property
import typing


def log_warning(msg, *args, **kwargs):
    Logger.get_instance().log_pyt_message('WARN', msg, *args, **kwargs)


def log_info(msg, *args, **kwargs):
    Logger.get_instance().log_pyt_message('INFO', msg, *args, **kwargs)


def log_error(msg, *args, **kwargs):
    Logger.get_instance().log_pyt_message('ERROR', msg, *args, **kwargs)


def log_debug(msg, *args, **kwargs):
    Logger.get_instance().log_pyt_message('DEBUG', msg, *args, **kwargs)


class Logger(QObject):

    __instance = None

    def __init__(self, parent: typing.Optional[QObject] = None) -> None:
        super().__init__(parent)
        if Logger.__instance is None:
            Logger.__instance = self

    @staticmethod
    def get_instance():
        if Logger.__instance is None:
            Logger()
        return Logger.__instance

    @Property(bool)
    def enabled(self):
        try:
            return self.__enabled
        except Exception:
            return False

    @enabled.setter
    def enabled(self, status):
        self.__enabled = status

    @property
    def console_log(self):
        try:
            return self.__console_log
        except Exception:
            return False

    @console_log.setter
    def console_log(self, status):
        self.__console_log = status

    def log_message(self, type: str, msg, *args, **kwargs):
        if self.enabled:
            if(type == 'ERROR'):
                logging.getLogger("KymoStudio").error(msg, *args, **kwargs)
            elif(type == 'WARN'):
                logging.getLogger("KymoStudio").warning(msg, *args, **kwargs)
            elif(type == 'INFO'):
                logging.getLogger("KymoStudio").info(msg, *args, **kwargs)
            elif(type == 'DEBUG'):
                logging.getLogger("KymoStudio").debug(msg, *args, **kwargs)
            elif(type == 'STACK'):
                logging.getLogger("KymoStudio").debug(msg, *args, **kwargs)
            else:
                logging.getLogger("KymoStudio").debug('INVALID LOG_TYPE: %s', msg)

        if self.console_log:
            try:
                rendered_message = str(msg) % args if args else str(msg)
            except (TypeError, ValueError):
                rendered_message = " ".join((str(msg), *(str(arg) for arg in args)))
            print("{oType} - {oMsg}".format(oType=type, oMsg=rendered_message))

    def log_qml_message(self, type: str, msg, *args, **kwargs):
        self.log_message(type, 'QML - {}'.format(msg), *args, **kwargs)

    def log_pyt_message(self, type: str, msg, *args, **kwargs):
        self.log_message(type, 'PYT - {}'.format(msg), *args, **kwargs)

    @Slot(str)
    def log_error(self, msg: str):
        Logger.get_instance().log_qml_message('ERROR', msg)

    @Slot(str)
    def log_warning(self, msg: str):
        Logger.get_instance().log_qml_message('WARN', msg)

    @Slot(str)
    def log_info(self, msg: str):
        Logger.get_instance().log_qml_message('INFO', msg)

    @Slot(str)
    def log_debug(self, msg: str):
        Logger.get_instance().log_qml_message('DEBUG', msg)

    @Slot(str)
    def log_qml_stack(self, stack_info):
        self.log_message("STACK", 'QML Stack - {}'.format(stack_info))

    def config(self, config: dict) -> None:
        """Use a bounded rotating log instead of an ever-growing project file."""
        self.enabled = bool(config.get("enabled", True))
        self.console_log = bool(config.get("console_log", False))
        log = logging.getLogger("KymoStudio")
        log.propagate = False
        level = getattr(logging, str(config.get("level", "INFO")).upper(), logging.INFO)
        log.setLevel(level if isinstance(level, int) else logging.INFO)
        for handler in list(log.handlers):
            log.removeHandler(handler)
            handler.close()
        if self.enabled:
            path = Path(config.get("name", "kymostudio.log"))
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                handler = RotatingFileHandler(path, maxBytes=2*1024*1024, backupCount=3, encoding="utf-8")
            except OSError:
                handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            log.addHandler(handler)


if __name__ == "__main__":
    config = {
        "enabled": 1,
        "name": "logfile.log",
        "level": "DEBUG"
    }

    x = Logger()
    x.config(config)

    log_warning("test 1,2,3")
    log_debug("laösdjflas")
