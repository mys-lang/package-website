#!/usr/bin/env python3

import os
import shutil
import pexpect
import requests
import subprocess
import systest
import logging


LOGGER = logging.getLogger(__name__)

PORT = 18000
BASE_URL = f'http://localhost:{PORT}'


class Logger:

    def __init__(self):
        self._data = ''

    def write(self, data):
        line = ''

        for char in self._data + data:
            if char == '\n':
                line = line.strip('\r\n\v')
                line = line.replace('\x1b', '')
                LOGGER.info('app: %s', line)
                line = ''
            else:
                line += char

        self._data = line

    def flush(self):
        pass


class TestCase(systest.TestCase):

    def http_get(self, path):
        return requests.get(f"{BASE_URL}{path}")

    def http_post(self, path, data):
        return requests.post(f"{BASE_URL}{path}", data=data)


class IndexTest(TestCase):
    """Get index page.

    """

    def run(self):
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('<title>The Mys Programming Language</title>', response.text)


class PackageOsTest(TestCase):
    """Various package operations and pages.

    """

    def run(self):
        with open('../os-0.16.0.tar.gz', 'rb') as fin:
            data = fin.read()

        # Download when not present.
        response = self.http_get("/package/os-0.16.0.tar.gz")
        self.assert_equal(response.status_code, 404)

        # Upload.
        response = self.http_post("/package/os-0.16.0.tar.gz", data)
        self.assert_equal(response.status_code, 200)

        # Download.
        response = self.http_get("/package/os-0.16.0.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, data)

        # Package page.
        response = self.http_get("/package/os")
        self.assert_equal(response.status_code, 200)
        self.assert_in('<title>os</title>', response.text)


def main():
    shutil.rmtree('storage', ignore_errors=True)
    os.mkdir('storage')
    os.chdir('storage')

    sequencer = systest.setup("Mys website",
                              console_log_level=logging.DEBUG)

    website = pexpect.spawn(f'../../build/speed/app --port {PORT}',
                            logfile=Logger(),
                            encoding='utf-8',
                            codec_errors='replace')
    website.expect_exact(f"Listening for clients on port {PORT}.")

    sequencer.run(
        IndexTest(),
        PackageOsTest())

    website.close()
    website.wait()
    sequencer.report_and_exit()


main()
