import os
import glob
import tempfile
import shutil
import subprocess
import platform
import tarfile
import time
from argparse import ArgumentParser
import requests
import html5lib
from ansi2html import Ansi2HTMLConverter
from xdg import xdg_cache_home


def list_all_packages(url):
    response = requests.get(f'{url}/standard-library.html')
    response.raise_for_status()
    document = html5lib.parse(response.text)
    NS = {'ns': 'http://www.w3.org/1999/xhtml'}
    packages = []

    for row in document.findall('.//ns:table/ns:tbody/ns:tr', NS):
        packages.append(row[0][0].text)

    return packages


def clear_cache():
    shutil.rmtree(xdg_cache_home() / 'mys/downloads', ignore_errors=True)


def add_all_packages_to_dependencies(packages):
    with open('stdall/package.toml', 'a') as fout:
        for package in packages:
            print(f'{package} = "latest"', file=fout)


def create_log_header(package_root):
    header = [
        f'Date:       {time.ctime()}'
    ]
    uname = platform.uname()
    header += [
        f'System:     {uname.system}',
        f'Node:       {uname.node}',
        f'Release:    {uname.release}',
        f'Version:    {uname.version}',
        f'Machine:    {uname.machine}',
        f'Processor:  {uname.processor}'
    ]
    mys_version = subprocess.run(['mys', '--version'],
                                 text=True,
                                 capture_output=True).stdout.strip()
    header += [
        f'MysVersion: {mys_version}'
    ]
    header += [
        f"Configuration:"
    ]

    with open(f"{package_root}/package.toml") as fin:
        header.append(fin.read().strip())

    return '\n'.join(header) + '\n\n'


def build_and_test_package(package, url, jobs):
    response = requests.get(f'{url}/package/{package}-latest.tar.gz')
    response.raise_for_status()

    with open('package-latest.tar.gz', 'wb') as fout:
        fout.write(response.content)

    with tarfile.open('package-latest.tar.gz') as fin:
        fin.extractall('package')

    print(f'========================= {package} =========================')
    package_root = glob.glob('package/*')[0]
    build_command = ['mys', '-C', package_root, 'build', '--url', url]

    if jobs is not None:
        build_command += ['-j', jobs]

    build_proc = subprocess.run(build_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

    test_command = ['mys', '-C', package_root, 'test', '-c', '--url', url]

    if jobs is not None:
        test_command += ['-j', jobs]

    test_proc = subprocess.run(test_command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    if build_proc.returncode == 0 and test_proc.returncode == 0:
        result = 'yes'
    else:
        result = 'no'

    if test_proc.returncode == 0:
        with tarfile.open('coverage.tar.gz', 'w:gz') as tar:
            tar.add(f'{package_root}/coverage')

        coverage = 'coverage.tar.gz'
    else:
        coverage = None

    header = create_log_header(package_root)
    log = header.encode('utf-8')
    log += f'$ {" ".join(build_command)}\n'.encode('utf-8')
    log += build_proc.stdout
    log += f'$ {" ".join(test_command)}\n'.encode('utf-8')
    log += test_proc.stdout

    return result, log, coverage


def create_html_log(log):
    lines = []

    for line in log.split(b'\n'):
        lines.append(line[line.rfind(b'\r') + 1:])

    log = b'\n'.join(lines)
    log = Ansi2HTMLConverter().convert(log.decode('utf-8'))

    return log


def upload_build_and_test_result(package, result, log, coverage, url):
    response = requests.post(
        f'{url}/standard-library/{package}/build-result.txt',
        data=result)
    response.raise_for_status()

    response = requests.post(
        f'{url}/standard-library/{package}/build-log.html',
        data=create_html_log(log).encode('utf-8'))
    response.raise_for_status()

    if coverage is not None:
        with open(coverage, 'rb') as fin:
            response = requests.post(
                f'{url}/standard-library/{package}/coverage.tar.gz',
                data=fin.read())
            response.raise_for_status()


def build_and_upload_package(package, url, jobs):
    with tempfile.TemporaryDirectory() as tempdir:
        original_dir = os.getcwd()
        os.chdir(tempdir)

        try:
            result, log, coverage = build_and_test_package(package, url, jobs)
            upload_build_and_test_result(package, result, log, coverage, url)
        finally:
            os.chdir(original_dir)


def main():
    parser = ArgumentParser()
    parser.add_argument('-u', '--url', default='https://mys-lang.org')
    parser.add_argument('-j', '--jobs')
    args = parser.parse_args()

    packages = list_all_packages(args.url)
    clear_cache()

    for package in packages:
        build_and_upload_package(package, args.url, args.jobs)


if __name__ == '__main__':
    main()
