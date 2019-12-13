import requests
import sys
import tempfile
import os
import json
import pandas as pd
import time

from argparse import ArgumentParser 
from urllib import parse
from bs4 import BeautifulSoup

bat_url_root = 'https://bringatrailer.com'

def cache_response(file_name, content):
    try:
        with open(file_name, "w") as f:
            f.write(content)
    except IOError:
        return False

    return True

def parse_titlesub(titlesub):
    return "Y" if (titlesub.lower().startswith("sold for")) else "N"

def main():
    parser = ArgumentParser(description='BaT price trend')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-f', type=str, dest='folder', help='name of folder in BaT or search term')
    action.add_argument('-u', type=str, dest='url', help="full url to page with information")
    parser.add_argument('-o', type=str, dest='output_file', help='output CSV file')

    args = parser.parse_args()
    url = None
    category = args.folder
    if args.url:
        url = args.url
        category = os.path.basename(os.path.normpath(parse.urlparse(url).path))
    else:
        url = f'{bat_url_root}/{category}'
    
    output_file = args.output_file
    if not output_file:
        output_file = f'./{category}.csv'

    cache_file = f'{tempfile.gettempdir()}/{category}.html'
    html_doc = None
    try:
        with open(cache_file) as f:
            html_doc = f.read()
            status_code = 200
            print(f'Reading from cache {cache_file} ...')
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
                if not cache_response(cache_file, html_doc):
                    print(f'Failed to cache response to {cache_file}')
                break
            else:
                # TODO cache failures 
                break

    if status_code != 200:
        print(f'Failed to download stats from {url} with code {status_code}')
        sys.exit(status_code)
    

    soup = BeautifulSoup(html_doc, 'html.parser') 
    # class="chart" attribute "data-stats" holds all the goodies
    result = soup.findAll("div", {"class": "chart"})
    data_stats = result[0].attrs['data-stats']
    root = json.loads(data_stats)
    data_points = root['s']
    # convert the json into Panda's handy DataFrame object for manipulation and
    # CSV serialization
    df = pd.io.json.json_normalize(data_points, max_level=1)
    # we only care about amount, timestamp, title, titlesub and url
    # titlesub tells us if the vehicle sold or not.
    df.drop(labels=['image', 'timestampms'], axis=1, inplace=True)

    # epoch to date
    # time.strftime('%Y-%m-%d', time.localtime(timestamp))
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y')

    # add the "sold" column based on the titlesub string
    df.insert(0, 'sold', None)
    df['sold'] = df.apply(lambda row: parse_titlesub(row['titlesub']), axis=1)
    
    # finally, sort the sucker
    df = df.sort_values(['amount'], ascending=[True])

    # outout to csv file        
    df.to_csv(output_file)
    print(f'Done: {output_file}')

if __name__ == "__main__":
    main()
