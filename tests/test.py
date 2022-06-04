import os
import sys
import shutil
import pexpect
import requests
import subprocess
import systest
import logging
import threading

from gql import gql
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import print_schema

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

    def http_post(self, path, data=None, params=None, json=None):
        return requests.post(f"{BASE_URL}{path}", data=data, params=params, json=json)

    def http_delete(self, path, params=None):
        return requests.delete(f"{BASE_URL}{path}", params=params)

    def subprocess_run(self, command):
        return subprocess.run(command, check=True, capture_output=True, text=True)


class FreshDatabaseTest(TestCase):
    """Test with a fresh database.

    """

    def run(self):
        response = self.http_get("/")
        self.assert_equal(response.status_code, 404)


class MysTest(TestCase):
    """Upload mys.

    """

    def run(self):
        # Upload.
        with open('mys-0.234.0.tar.gz', 'rb') as fin:
            data = fin.read()

        response = self.http_post("/mys-0.234.0.tar.gz", data)
        self.assert_equal(response.status_code, 200)
        token = response.json()['token']

        # Index exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('The Mys programming language', response.text)
        self.assert_in('0.234.0', response.text)
        self.assert_not_in('0.267.0', response.text)

        # Upload the same release a few more times.
        for _ in range(3):
            response = self.http_post("/mys-0.234.0.tar.gz",
                                      data,
                                      params={'token': token})
            self.assert_equal(response.status_code, 200)
            self.assert_equal(response.text, '')

        # Index still exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('The Mys programming language', response.text)

        # Upload a new version.
        with open('mys-0.267.0.tar.gz', 'rb') as fin:
            data = fin.read()

        response = self.http_post("/mys-0.267.0.tar.gz",
                                  data,
                                  params={'token': token})
        self.assert_equal(response.status_code, 200)

        # Index exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('The Mys programming language', response.text)
        self.assert_not_in('0.234.0', response.text)
        self.assert_in('0.267.0', response.text)

        # Upload older version again. New should still be used.
        with open('mys-0.234.0.tar.gz', 'rb') as fin:
            data = fin.read()

        response = self.http_post("/mys-0.234.0.tar.gz",
                                  data,
                                  params={'token': token})
        self.assert_equal(response.status_code, 200)

        # Index exists.
        response = self.http_get("/")
        self.assert_equal(response.status_code, 200)
        self.assert_in('The Mys programming language', response.text)
        self.assert_not_in('0.234.0', response.text)
        self.assert_in('0.267.0', response.text)


class PackageTest(TestCase):
    """Various package operations and pages.

    """

    def run(self):
        shutil.rmtree("foo", ignore_errors=True)
        self.subprocess_run(["mys", "new", "foo"])

        package_list_item = '<a href="/package/foo/latest/index.html">foo</a>'
        package_activity_message = (
            'Package <a href="/package/foo/latest/index.html">foo</a> '
            'version 0.1.0 released.')

        # Package page does not exist.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 404)

        response = self.http_get("/package/foo/latest/index.html")
        self.assert_equal(response.status_code, 404)

        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in(package_list_item, response.text)

        response = self.http_get("/activity.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in(package_activity_message, response.text)

        # Download when not present.
        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 404)

        # Upload.
        proc = self.subprocess_run(["mys", "-C", "foo", "publish", "-a", BASE_URL])
        token = proc.stdout.rstrip()[-64:]

        # Download specific version and latest.
        with open('foo/build/publish/foo-0.1.0.tar.gz', 'rb') as fin:
            expected_data = fin.read()

        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, expected_data)

        response = self.http_get("/package/foo-latest.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, expected_data)

        # Package page.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Foo 0.1.0 documentation', response.text)

        response = self.http_get("/package/foo/latest/index.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Foo 0.1.0 documentation', response.text)

        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in(package_list_item, response.text)

        response = self.http_get("/activity.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in(package_activity_message, response.text)

        # Upload the package again without a token.
        with self.assert_raises(subprocess.CalledProcessError):
            self.subprocess_run(["mys", "-C", "foo", "publish", "-a", BASE_URL])

        # Upload the package again with wrong token.
        with self.assert_raises(subprocess.CalledProcessError):
            self.subprocess_run(["mys", "-C", "foo", "publish",
                                 "-a", BASE_URL,
                                 "-t", 64 * "0"])

        # Upload the package again with correct token.
        self.subprocess_run(["mys", "-C", "foo", "publish",
                             "-a", BASE_URL,
                             "-t", token])

        # Try to delete the package with wrong token.
        response = self.http_delete(f'/package/foo', params={'token': 64 * '0'})
        self.assert_equal(response.status_code, 401)

        # Package page.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Foo 0.1.0 documentation', response.text)

        # Delete the package.
        response = self.http_delete(f'/package/foo', params={'token': token})
        self.assert_equal(response.status_code, 200)

        # Package page does not exist.
        response = self.http_get("/package/foo/0.1.0/index.html")
        self.assert_equal(response.status_code, 404)

        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in(package_list_item, response.text)

        # Download when not present.
        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 404)

        # Upload again.
        proc = self.subprocess_run(["mys", "-C", "foo", "publish", "-a", BASE_URL])
        assert proc.stdout.rstrip()[-64:] != token

        # Download it.
        with open('foo/build/publish/foo-0.1.0.tar.gz', 'rb') as fin:
            expected_data = fin.read()

        response = self.http_get("/package/foo-0.1.0.tar.gz")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.content, expected_data)

        # No build information available.
        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in('✅', response.content.decode('utf-8'))
        self.assert_not_in('❌', response.content.decode('utf-8'))
        self.assert_in('🤔', response.content.decode('utf-8'))

        # Upload package build results.
        response = self.http_post("/standard-library/foo/build-result.txt",
                                  data='yes')
        self.assert_equal(response.status_code, 200)

        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('✅', response.content.decode('utf-8'))
        self.assert_not_in('❌', response.content.decode('utf-8'))
        self.assert_not_in('🤔', response.content.decode('utf-8'))

        # Upload package build results.
        response = self.http_post("/standard-library/foo/build-result.txt",
                                  data='no')
        self.assert_equal(response.status_code, 200)

        response = self.http_get("/standard-library.html")
        self.assert_equal(response.status_code, 200)
        self.assert_not_in('✅', response.content.decode('utf-8'))
        self.assert_in('❌', response.content.decode('utf-8'))
        self.assert_not_in('🤔', response.content.decode('utf-8'))

        # Upload package build log.
        response = self.http_post("/standard-library/foo/build-log.html",
                                  data=b'<html>The foo log!</html>')
        self.assert_equal(response.status_code, 200)

        response = self.http_get("/standard-library/foo/build-log.html")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(b'<html>The foo log!</html>', response.content)


class UpdateBuildResultsTest(TestCase):
    """Update the build result for the foo package.

    """

    def run(self):
        shutil.rmtree('stdall', ignore_errors=True)
        self.subprocess_run([
            sys.executable,
            'update_standard_library_build_results.py',
            '--url', BASE_URL
        ])

        response = self.http_get("/standard-library/foo/build-log.html")
        self.assert_equal(response.status_code, 200)
        text = response.text
        self.assert_equal(text.count('Reading package configuration'), 2)
        self.assert_equal(text.count('Building'), 2)


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


class PackageDependentsTest(TestCase):
    """Package dependents.

    """

    def publish_new_package(self, name):
        shutil.rmtree(name, ignore_errors=True)
        self.subprocess_run(["mys", "new", name])
        self.subprocess_run(["mys", "-C", name, "publish", "-a", BASE_URL])

    def run(self):
        self.publish_new_package("deps_b")
        self.publish_new_package("deps_c")

        shutil.rmtree("deps_a", ignore_errors=True)
        self.subprocess_run(["mys", "new", "deps_a"])

        with open("deps_a/package.toml") as fin:
            config = fin.read()

        config += '\n'
        config += 'deps_b = "latest"\n'
        config += 'deps_c = "latest"\n'

        with open("deps_a/package.toml", 'w') as fout:
            fout.write(config)

        self.subprocess_run(["mys", "-C", "deps_a", "publish", "-a", BASE_URL])

        response = self.http_get("/standard-library/deps_a/dependents.txt")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.text, "")
        response = self.http_get("/standard-library/deps_b/dependents.txt")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.text, "deps_a\n")
        response = self.http_get("/standard-library/deps_c/dependents.txt")
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.text, "deps_a\n")
        response = self.http_get("/standard-library/deps_d/dependents.txt")
        self.assert_equal(response.status_code, 404)


class PackageListTest(TestCase):
    """List packages.

    """

    def publish_new_package(self, name):
        shutil.rmtree(name, ignore_errors=True)
        self.subprocess_run(["mys", "new", name])
        self.subprocess_run(["mys", "-C", name, "publish", "-a", BASE_URL])

    def run(self):
        self.publish_new_package("list_a")
        self.publish_new_package("list_b")

        response = self.http_get("/standard-library/list.txt")
        self.assert_equal(response.status_code, 200)
        self.assert_in('list_a', response.text)
        self.assert_in('list_b', response.text)


class GraphQLTest(TestCase):
    """GraphQL tests.

    """

    def publish_new_package(self, name):
        shutil.rmtree(name, ignore_errors=True)
        self.subprocess_run(["mys", "new", name])
        self.subprocess_run(["mys", "-C", name, "publish", "-a", BASE_URL])

    def create_graphql_client(self):
        transport = AIOHTTPTransport(url=f"{BASE_URL}/graphql")

        return Client(transport=transport, fetch_schema_from_transport=True)

    def run(self):
        self.publish_new_package("graphql_a")
        self.publish_new_package("graphql_b")

        client = self.create_graphql_client()

        result = client.execute(
            gql("query MyQuery {"
                "  standardLibrary {"
                "    numberOfDownloads"
                "    numberOfPackages"
                "    package(name: \"graphql_b\") {"
                "      builds"
                "      coverage"
                "      latestRelease {"
                "        version"
                "        description"
                "      }"
                "      name"
                "      numberOfDownloads"
                "      linesOfCode {"
                "        languages {"
                "          name"
                "          data {"
                "            files"
                "            blank"
                "            comment"
                "            code"
                "          }"
                "        }"
                "        total {"
                "          files"
                "          blank"
                "          comment"
                "          code"
                "        }"
                "      }"
                "    }"
                "    packages {"
                "      builds"
                "      coverage"
                "      latestRelease {"
                "        description"
                "        version"
                "      }"
                "      name"
                "      numberOfDownloads"
                "    }"
                "  }"
                "  statistics {"
                "    noIdleClientHandlers"
                "    numberOfGraphqlRequests"
                "    numberOfUniqueVisitors"
                "    startDateTime"
                "    totalNumberOfRequests"
                "  }"
                "  activities {"
                "    date"
                "    kind"
                "    message"
                "  }"
                "}"))

        standard_library = result['standardLibrary']
        self.assert_greater_equal(standard_library['numberOfPackages'], 2)
        self.assert_greater_equal(standard_library['numberOfDownloads'], 2)

        packages = standard_library['packages']
        package_names = [package['name']for package in packages]
        self.assert_in('graphql_a', package_names)
        self.assert_in('graphql_b', package_names)

        package = result['standardLibrary']['package']
        self.assert_equal(package['name'], 'graphql_b')
        self.assert_equal(package['latestRelease']['version'], '0.1.0')
        languages = package['linesOfCode']['languages']
        self.assert_greater_equal(languages[0]['data']['files'], 1)
        self.assert_greater_equal(languages[0]['data']['blank'], 1)
        self.assert_greater_equal(languages[0]['data']['comment'], 1)
        self.assert_greater_equal(languages[0]['data']['code'], 1)
        self.assert_greater_equal(languages[1]['data']['files'], 1)
        total = package['linesOfCode']['total']
        self.assert_greater_equal(total['files'], 1)
        self.assert_greater_equal(total['blank'], 1)
        self.assert_greater_equal(total['comment'], 1)
        self.assert_greater_equal(total['code'], 1)

        statistics = result['statistics']
        self.assert_greater_equal(statistics['totalNumberOfRequests'], 0)
        self.assert_equal(statistics['numberOfUniqueVisitors'], 0)
        self.assert_equal(statistics['numberOfGraphqlRequests'], 2)
        self.assert_equal(statistics['noIdleClientHandlers'], 0)

        activities = result['activities']
        self.assert_in('date', activities[0])
        kinds = [activity['kind'] for activity in activities]
        self.assert_in("✨", kinds)
        self.assert_in("📦", kinds)
        self.assert_in("🐭", kinds)
        messages = [
            activity['message']
            for activity in activities
            if activity['kind'] == "📦"
        ]
        self.assert_in("Package ", messages[0])

        with open('../assets/schema.graphql', 'r') as fin:
            self.assert_equal(print_schema(client.schema) + '\n', fin.read())

class StatisticsTest(TestCase):

    def run(self):
        response = self.http_get("/statistics.html")
        self.assert_equal(response.status_code, 200)
        self.assert_in('Statistics', response.text)
        self.assert_in('Start date and time', response.text)
        self.assert_in('Traffic', response.text)
        self.assert_in('<td>/standard-library/foo/build-log.html</td>', response.text)
        self.assert_in('svg', response.text)
        response = self.http_get("/_images/world.svg")
        self.assert_equal(response.status_code, 200)


class ResponseContentTypeJsTest(TestCase):

    def run(self):
        response = self.http_get('/searchindex.js')
        self.assert_equal(response.status_code, 200)
        self.assert_equal(response.headers['content-type'], 'application/javascript')


def main():
    sequencer = systest.setup("Mys website",
                              console_log_level=logging.DEBUG)

    shutil.rmtree('storage', ignore_errors=True)
    website = pexpect.spawn(f'../build/speed-coverage/app --port {PORT} -d storage',
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
        UpdateBuildResultsTest(),
        PackageNoDocTest(),
        StatisticsTest(),
        ResponseContentTypeJsTest(),
        PackageDependentsTest(),
        PackageListTest(),
        GraphQLTest()
    )

    website.sendintr()
    website.wait()
    sequencer.report_and_exit()


main()
