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


class IndexTest(systest.TestCase):
    """Get index page.

    """

    def run(self):
        response = requests.get(BASE_URL)
        self.assert_equal(response.status_code, 200)
        self.assert_in('<title>The Mys Programming Language</title>', response.text)


class PackageOsTest(systest.TestCase):
    """Various package operations and pages.

    """

    def run(self):
        with open('../os-0.16.0.tar.gz', 'rb') as fin:
            data = fin.read()

        # Download when not present.
        response = requests.get(f"{BASE_URL}/package/os-0.16.0.tar.gz")
        self.assert_not_equal(response.status_code, 200)

        # Upload.
        response = requests.post(f"{BASE_URL}/package/os-0.16.0.tar.gz",
                                 data=data)
        self.assert_equal(response.status_code, 200)

        # Download.
        response = requests.get(f"{BASE_URL}/package/os-0.16.0.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, data)

        # Package page.
        response = requests.get(f"{BASE_URL}/package/os")
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
