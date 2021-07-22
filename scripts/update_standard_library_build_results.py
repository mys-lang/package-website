import subprocess
import requests
import html5lib


def list_all_packages():
    response = requests.get('https://mys-lang.org/standard-library.html')
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


def build_package(package):
    print(f'========================= {package} =========================')
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

    return result, proc.stdout


def upload_build_result_and_log(package, result, log):
    response = requests.post(
        f'https://mys-lang.org/standard-library/{package}/build-result.txt',
        data=result)
    response.raise_for_status()

    response = requests.post(
        f'https://mys-lang.org/standard-library/{package}/build-log.txt',
        data=log)
    response.raise_for_status()


def build_and_upload_package(package):
    result, log = build_package(package)
    upload_build_result_and_log(package, result, log)

def main():
    packages = list_all_packages()
    subprocess.run(['mys', 'new', 'all'], check=True)
    add_all_packages_to_dependencies(packages)
    subprocess.run(['mys', '-C', 'all', 'build'])

    for package in packages:
        build_and_upload_package(package)


if __name__ == '__main__':
    main()
