import requests
import sys
import tempfile
import os

from argparse import ArgumentParser 
from urllib import parse
from html.parser import HTMLParser

bat_url_root = 'https://bringatrailer.com'

def cache_response(file_name, content):
    try:
        with open(file_name, "w") as f:
            f.write(content)
    except IOError:
        return False

    return True

def main():
    parser = ArgumentParser(description='BaT price trend')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-f', type=str, dest='folder', help='name of folder in BaT or search term')
    action.add_argument('-u', type=str, dest='url', help="full url to page with information")

    args = parser.parse_args()
    url = None
    category = args.folder
    if args.url:
        url = args.url
        category = os.path.basename(os.path.normpath(parse.urlparse(url).path))
    else:
        url = f'{bat_url_root}/{category}'
    
    save_to_file = f'{tempfile.gettempdir()}/{category}.html'
    html_doc = None
    try:
        with open(save_to_file) as f:
            html_doc = f.read()
            status_code = 200
            print(f'Reading from cache {save_to_file} ...')
    except IOError:    
        status_code = -1
        while True:
            r = requests.get(url)
            status_code = r.status_code
            if status_code == 302:
                url = r.headers['location']
            elif status_code == 200:
                print(f'Downloaded {url}')
                html_doc = r.text
                if not cache_response(save_to_file, html_doc):
                    print(f'Failed to cache response to {save_to_file}')
                break
            else:
                # TODO cache failures 
                break

    if status_code != 200:
        print(f'Failed to download stats from {url} with code {status_code}')
        sys.exit(status_code)
    
    # "data-stats" holds all the goodies
    # print(f"{html_doc}")
    

if __name__ == "__main__":
    main()
