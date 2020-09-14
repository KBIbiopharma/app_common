from logging import Handler
from datetime import datetime
import requests
from uuid import uuid4

from app_common.std_lib.os_utils import collect_user_name


class RequestsHTTPHandler(Handler):
    """ Custom HTTPHandler passing the HTTP request using the requests.post
    method, since it tends to be more stable for REST API end points.
    """
    def __init__(self, url, app_name="", session_start="", username="",
                 dt_fmt="", debug=False, **adtl_data):
        """ Initialize the instance with the request URL and all parameters.
        """
        super(RequestsHTTPHandler, self).__init__()

        if not dt_fmt:
            dt_fmt = "%Y/%m/%d %H:%M:%S"

        self.url = url
        self.app_name = app_name
        self.adtl_data = adtl_data
        # This log_id should be unique and constant throughout a tool
        # usage:
        self.session_id = app_name + ":" + username + ":" + session_start
        self.username = username
        self.dt_fmt = dt_fmt
        self.debug = debug

    def emit(self, record):
        """ Custom implementation of emit using requests.post since it tends to
        work more easily with REST API end points.
        """
        data = self.map_log_record(record)
        # Build a valid json string with the data to record:
        payload = self.build_payload(data)
        response = requests.post(self.url, data=payload)
        if self.debug:
            print(response.content)
        return response

    def map_log_record(self, record):
        """ Custom implementation of mapping the log record into a dict.
        """
        # Generate utc datetime since default logging collects local time:
        utc_datetime = datetime.strftime(datetime.utcnow(), self.dt_fmt)
        data = {
            "log_id": str(uuid4()),
            "session_id": self.session_id,
            "app_name": self.app_name,
            'user': self.username,
            "pkg": record.name,
            'level_no': record.levelno,
            'line_no': record.lineno,
            'func_name': record.funcName,
            'utc_timestamp': utc_datetime,
            'msg': self.clean_msg(record.msg)
        }
        data.update(self.adtl_data)
        return data

    def build_payload(self, data):
        """ Convert dict of data to valid json string to send through HTTP. """
        return str(data).replace("'", '"')

    def clean_msg(self, msg):
        """ Clean logging message to make it HTTP compatible. """
        return msg.replace("'", " ")
