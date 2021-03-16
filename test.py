import os
import shutil
import pexpect
import requests
import subprocess
import systest
import logging


LOGGER = logging.getLogger(__name__)


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
        response = requests.get("http://localhost:18000/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('<title>The Mys Programming Language</title>', response.text)


class PackageTest(systest.TestCase):
    """Get a package page.

    """

    def run(self):
        response = requests.get("http://localhost:18000/package/os")
        self.assert_equal(response.status_code, 200)
        self.assert_in('<title>os</title>', response.text)


def main():
    shutil.rmtree('test', ignore_errors=True)
    os.mkdir('test')
    os.chdir('test')

    sequencer = systest.setup("Mys website",
                              console_log_level=logging.DEBUG)

    website = pexpect.spawn('../build/speed/app --port 18000',
                            logfile=Logger(),
                            encoding='utf-8',
                            codec_errors='replace')
    website.expect_exact("Listening for clients on port 18000.")

    sequencer.run(
        IndexTest(),
        PackageTest()
    )

    sequencer.report_and_exit()


main()
