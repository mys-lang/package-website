import subprocess
import platform
import time
from argparse import ArgumentParser
import requests
import html5lib
from ansi2html import Ansi2HTMLConverter


def list_all_packages(url):
    response = requests.get(f'{url}/standard-library.html')
    response.raise_for_status()
    document = html5lib.parse(response.text)
    NS = {'ns': 'http://www.w3.org/1999/xhtml'}
    packages = []

    for row in document.findall('.//ns:table/ns:tbody/ns:tr', NS):
        packages.append(row[0][0].text)

    return packages


def add_all_packages_to_dependencies(packages):
    with open('all/package.toml', 'a') as fout:
        for package in packages:
            print(f'{package} = "latest"', file=fout)


def create_log_header():
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

    return '\n'.join(header) + '\n\n'


def build_package(package):
    print(f'========================= {package} =========================')
    header = create_log_header()
    command = [
        'mys',
        '-C', f'all/build/dependencies/{package}-latest',
        'build'
    ]
    proc = subprocess.run(command,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)

    if proc.returncode == 0:
        result = 'yes'
    else:
        result = 'no'

    log = header.encode('utf-8')
    log += f'$ {" ".join(command)}\n'.encode('utf-8')
    log += proc.stdout

    return result, log


def create_html_log(log):
    lines = []

    for line in log.split(b'\n'):
        lines.append(line[line.rfind(b'\r') + 1:])

    log = b'\n'.join(lines)
    log = Ansi2HTMLConverter().convert(log.decode('utf-8'))

    return log


def upload_build_result_and_log(package, result, log, url):
    response = requests.post(
        f'{url}/standard-library/{package}/build-result.txt',
        data=result)
    response.raise_for_status()

    response = requests.post(
        f'{url}/standard-library/{package}/build-log.html',
        data=create_html_log(log).encode('utf-8'))
    response.raise_for_status()


def build_and_upload_package(package, url):
    result, log = build_package(package)
    upload_build_result_and_log(package, result, log, url)


def main():
    parser = ArgumentParser()
    parser.add_argument('-u', '--url', default='https://mys-lang.org')
    args = parser.parse_args()

    packages = list_all_packages(args.url)
    subprocess.run(['mys', 'new', 'all'], check=True)
    add_all_packages_to_dependencies(packages)
    subprocess.run(['mys', '-C', 'all', 'fetch', '--url', args.url], check=True)

    for package in packages:
        build_and_upload_package(package, args.url)


if __name__ == '__main__':
    main()
