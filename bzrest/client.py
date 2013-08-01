import logging
import json
from urlparse import urljoin

import requests

from .errors import BugzillaAPIError

log = logging.getLogger(__name__)


class BugzillaClient(object):
    def configure(self, bzurl, username, password):
        self.bzurl = bzurl
        if not self.bzurl.endswith("/"):
            self.bzurl += "/"
        self.username = username
        self.password = password

    def request(self, method, path, data=None):
        url = urljoin(self.bzurl, path)
        params = {
            "Bugzilla_login": self.username,
            "Bugzilla_password": self.password,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if data:
            data = json.dumps(data)
        log.info("Sending request: %s %s", method, url)
        log.debug("Data is: %s", data)
        r = requests.request(method, url, params=params, data=data, headers=headers)
        r.raise_for_status()
        # Bugzilla's REST API doesn't always return 4xx when it maybe should.
        # (Eg, loading a non-existent bug returns 200). We need to check the
        # response to know for sure whether or not there was an error.
        resp = r.json()
        log.info("Got response: %s", r.status_code)
        log.debug("Response body: %s", resp)
        if resp.get("error", False):
            raise BugzillaAPIError(resp["code"], resp["message"], response=resp)
        return resp

    def create_bug(self, data):
        return self.request("POST", "bug", data)

    def get_bug(self, id_, data=None):
        return self.request("GET", "bug/%s" % id_, data)["bugs"][0]

    def update_bug(self, id_, data):
        return self.request("POST", "bug/%s" % id_, data)

    def add_comment(self, id_, comment, data={}):
        data = data.copy()
        data["comment"] = comment
        return self.request("POST", "bug/%s/comment" % id_, data)
