"""Common utils for logging used across the codebase."""
import contextvars
import logging.config
import os
import traceback

import yaml

request_id_var = contextvars.ContextVar("request_id", default="no-request-id")


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def initialize_logger(logger_name: str) -> logging.Logger:
    """Utility function to intialize and return a logging object."""
    pwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    with open(os.path.join(pwd, "presets", "logging", "config.yaml"), "r") as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
    return logging.getLogger(logger_name)


def log_exceptions(logger: ..., exceptionObj: ...):
    """Utility to add exceptions related logs."""
    err_trace = "\n".join(
        traceback.format_exception(
            exceptionObj, value=exceptionObj, tb=exceptionObj.__traceback__
        )
    )
    logger.error(f"The full traceback is:\n{err_trace}")
