#!/usr/bin/env python3

import os
import shutil
import pexpect
import requests
import subprocess
import systest
import logging
import threading

LOGGER = logging.getLogger(__name__)

PORT = 18000
BASE_URL = f'http://localhost:{PORT}'


class WebsiteReaderThread(threading.Thread):

    def __init__(self, website):
        super().__init__()
        self.website = website
        self.daemon = True

    def run(self):
        try:
            while True:
                self.website.readline()
        except:
            pass


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


class FreshDatabaseTest(TestCase):
    """Test with a fresh database.

    """

    def run(self):
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('<html>No mys documentation found!</html>', response.text)


class MysTest(TestCase):
    """Upload mys.

    """

    def run(self):
        # Upload.
        with open('mys-0.227.0.tar.gz', 'rb') as fin:
            data = fin.read()

        response = self.http_post("/mys-0.227.0.tar.gz", data)
        self.assert_equal(response.status_code, 200)

        # Index exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Welcome to Mys’ documentation!', response.text)

        # Upload the same release a few more times.
        for _ in range(3):
            response = self.http_post("/mys-0.227.0.tar.gz", data)
            self.assert_equal(response.status_code, 200)

        # Index still exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Welcome to Mys’ documentation!', response.text)


class PackageTest(TestCase):
    """Various package operations and pages.

    """

    def run(self):
        shutil.rmtree("foo", ignore_errors=True)
        subprocess.run(["mys", "new", "foo"], check=True)
        subprocess.run(["mys", "-C", "foo", "publish", "-a", BASE_URL])

        with open('foo/build/publish/foo-0.1.0.tar.gz', 'rb') as fin:
            data = fin.read()

        package_list_item = (
            '<li><p><a href="/package/foo/0.1.0/index.html">foo</a> - '
            'Add a short package description here.</p></li>')

        # Package page does not exist.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 404)

        response = self.http_get("/0.227.0/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in(package_list_item, response.text)

        # Download when not present.
        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 404)

        # Upload.
        response = self.http_post("/package/foo-0.1.0.tar.gz", data)
        self.assert_equal(response.status_code, 200)

        # Download.
        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, data)

        # Package page.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Foo 0.1.0 documentation', response.text)

        response = self.http_get("/0.227.0/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in(package_list_item, response.text)


class PackageNoDocTest(TestCase):

    def run(self):
        with open('bar-0.3.0.tar.gz', 'rb') as fin:
            data = fin.read()

        # Package page does not exist.
        response = self.http_get("/package/bar/0.3.0/index.html")
        self.assert_equal(response.status_code, 404)

        # Upload.
        response = self.http_post("/package/bar-0.3.0.tar.gz", data)
        self.assert_equal(response.status_code, 200)

        # Package page.
        response = self.http_get("/package/bar/0.3.0/index.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('No package documentation found!', response.text)


def main():
    sequencer = systest.setup("Mys website",
                              console_log_level=logging.DEBUG)

    shutil.rmtree('storage', ignore_errors=True)
    website = pexpect.spawn(f'../build/speed/app --port {PORT} -d storage',
                            logfile=Logger(),
                            encoding='utf-8',
                            codec_errors='replace')
    website.expect_exact(f"Listening for clients on port {PORT}.")
    website_reader_thread = WebsiteReaderThread(website)
    website_reader_thread.start()

    sequencer.run(
        FreshDatabaseTest(),
        MysTest(),
        PackageTest(),
        PackageNoDocTest()
    )

    website.close()
    website.wait()
    sequencer.report_and_exit()


main()
