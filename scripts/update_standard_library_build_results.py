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


def build_packages(packages):
    results = {}

    for package in packages:
        print(f'========================= {package} =========================')
        proc = subprocess.run([
            'mys',
            '-C', f'all/build/dependencies/{package}-latest',
            'build'
        ])

        if proc.returncode == 0:
            result = 'pass'
        else:
            result = 'fail'

        results[package] = result

    for package, result in results.items():
        print(f'{package}: {result}')

    return results


def upload_build_results(results):
    response = requests.post(
        'https://mys-lang.org/standard-library/build-results.json',
        json=results)
    response.raise_for_status()


def main():
    packages = list_all_packages()
    subprocess.run(['mys', 'new', 'all'], check=True)
    add_all_packages_to_dependencies(packages)
    subprocess.run(['mys', '-C', 'all', 'build'])
    results = build_packages(packages)
    upload_build_results(results)


if __name__ == '__main__':
    main()
