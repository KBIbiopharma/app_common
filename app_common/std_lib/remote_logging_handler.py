from logging import Handler
from datetime import datetime
import requests
from uuid import uuid4

from app_common.std_lib.os_utils import collect_user_name


class CustomHTTPHandler(Handler):
    """ Custom HTTPHandler passing the HTTP request using the requests.post
    method, since it tends to be more stable for REST API end points.
    """
    def __init__(self, url, app_name="", start_dt="", dt_fmt="", **adtl_data):
        """ Initialize the instance with the request URL and all parameters.
        """
        super(CustomHTTPHandler, self).__init__()
        self.url = url
        self.app_name = app_name
        self.adtl_data = adtl_data
        self.start_dt = start_dt
        self.dt_fmt = dt_fmt

    def emit(self, record):
        """ Custom implementation of emit using requests.post since it tends to
        work more easily with REST API end points.
        """
        data = self.map_log_record(record)
        # Build a valid json string with the data to record:
        data_str = str(data).replace("'", '"')
        response = requests.post(self.url, data=data_str)
        return response

    def map_log_record(self, record):
        """ Custom implementation of mapping the log record into a dict.
        """
        # Generate utc datetime since default logging collects local time:
        utc_datetime = datetime.strftime(datetime.utcnow(), self.dt_fmt)
        username = collect_user_name()
        # This log_id should be unique and constant throughout a tool
        # usage:
        session_id = self.app_name + ":" + username + ":" + self.start_dt
        data = {
            "log_id": str(uuid4()),
            "session_id": session_id,
            "app_name": self.app_name,
            'user': username,
            "pkg": record.name,
            'level_no': record.levelno,
            'line_no': record.lineno,
            'func_name': record.funcName,
            'utc_timestamp': utc_datetime,
            'msg': record.msg
        }
        data.update(self.adtl_data)

        return data
