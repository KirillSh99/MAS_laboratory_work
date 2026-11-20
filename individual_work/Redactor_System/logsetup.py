import logging
from datetime import datetime


class actorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return "actorAddress" in logrecord.__dict__


class notActorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return "actorAddress" not in logrecord.__dict__


class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno != logging.INFO


logcfg = {
    "version": 1,
    "formatters": {
        "log": {"format": "%(asctime)s | %(levelname)-8s:  => %(message)s"},
        "plantuml": {"format": "%(message)s"},
    },
    "filters": {
        "isActorLog": {"()": actorLogFilter},
        "notActorLog": {"()": notActorLogFilter},
        "debugOnly": {"()": DebugOnlyFilter},
    },
    "handlers": {
        "h1": {
            "class": "logging.StreamHandler",
            "formatter": "log",
            "level": logging.DEBUG,
        },
        "h2": {
            "class": "logging.FileHandler",
            "filename": datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"),
            "formatter": "log",
            "level": logging.INFO,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {"handlers": ["h1", "h2"], "level": logging.DEBUG},
    },
}
