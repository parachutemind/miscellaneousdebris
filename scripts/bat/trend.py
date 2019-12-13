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

BAT_URL_ROOT = 'https://bringatrailer.com'
DEFAULT_WAIT_INTERVAL_SECS = 30

def cache_response(file_name, content):
    try:
        with open(file_name, "w") as f:
            f.write(content)
    except IOError:
        return False

    return True

def download_content(url, root_dir):
    html_doc = None
    page_name = os.path.basename(os.path.normpath(parse.urlparse(url).path))
    dir_name = os.path.dirname(os.path.normpath(parse.urlparse(url).path))
    cache_dir = f'{root_dir}/{dir_name}'
    os.makedirs(cache_dir, exist_ok=True) 
    cache_file = f'{cache_dir}/{page_name}.html'
    try:
        with open(cache_file) as f:
            html_doc = f.read()
            # TODO: Be nice and implement proper caching so the server can return 304 in addition to our local cache
            # and do away with the -f flag
            status_code = 304 # overload it for now and return something else once we implement support for 304
            print(f'Reading from cache {cache_file} ...')
    except IOError:    
        status_code = -1
        while True:
            # TODO: Be nice and implement proper caching so the server can return 302 in addition to our local cache
            # and do away with the -f flag
            r = requests.get(url)
            status_code = r.status_code
            if status_code == 302:
                url = r.headers['location']
            elif status_code == 200:
                print(f'Downloaded {url}:{cache_file}')
                html_doc = r.text
                if not cache_response(cache_file, html_doc):
                    print(f'Failed to cache response to {cache_file}')
                break
            else:
                # TODO collect error stats, cache upto N failures and then try again? 
                break
    return status_code, html_doc

def follow_listings(df, wait, cache_dir):
    for _, row in df.iterrows():
        url = row['url']
        res, html_doc = download_content(url, cache_dir)
        if isHttpOk(res):
            # extract information and add it to df.
            pass
        else:
            # TODO count errors
            pass
        
        if res == 200:
            time.sleep(wait)

def parse_titlesub(titlesub):
    return "Y" if (titlesub.lower().startswith("sold for")) else "N"

def isHttpOk(status):
    return status == 200 or status == 304

def main():
    parser = ArgumentParser(description='BaT price trend')
    # action = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-u', type=str, dest='url', required=True, help="full url to page with information")
    parser.add_argument('-o', type=str, dest='output_file', help='(optional) output CSV file')
    parser.add_argument('-dont-follow', action='store_true', help="Don't follow listings to extract additional info")
    parser.add_argument('-f', action='store_true', dest='force_download', help="Force download, don't use local cached files")
    parser.add_argument('-wait', type=int, default=2, help=f'When following listings, wait specified seconds before hitting the next listing. Min and default is {DEFAULT_WAIT_INTERVAL_SECS}')

    args = parser.parse_args()
    if args.force_download:
        print("-f NYI")
        sys.exit(-1)

    if args.wait < DEFAULT_WAIT_INTERVAL_SECS:
        args.wait = DEFAULT_WAIT_INTERVAL_SECS

    # TODO: turn all this into properties of a class that is then used within main... for now quick and dirty wins, sorry TDD ;)     
    category = os.path.basename(os.path.normpath(parse.urlparse(args.url).path))
    output_file = args.output_file
    if not output_file:
        output_file = f'./{category}.csv'
    
    cache_dir = tempfile.gettempdir()
    status_code, html_doc = download_content(args.url, cache_dir)
    if not isHttpOk(status_code):
        print(f'Failed to download stats from {args.url} with code {status_code}')
        sys.exit(status_code)
    
    soup = BeautifulSoup(html_doc, 'html.parser') 
    # class="chart" attribute "data-stats" holds all the goodies
    result = soup.findAll("div", {"class": "chart"})
    data_stats = result[0].attrs['data-stats']
    root = json.loads(data_stats)
    # 's' is for sold, 'u' is for not sold, i will just use the 'titlesub' later to differentiate the 2. 
    # TODO: change this later to use the 's' and 'u' correctly 
    sold = root['s']
    not_sold = root['u']
    # convert the json into Panda's handy DataFrame object for manipulation and
    # CSV serialization
    df = pd.io.json.json_normalize(sold, max_level=1)
    df = df.append(pd.io.json.json_normalize(not_sold, max_level=1))

    # epoch to date
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y')

    # add the "sold" column based on the titlesub string
    df.insert(0, 'sold', None)
    df.insert(4, 'year', None)
    df['sold'] = df.apply(lambda row: parse_titlesub(row['titlesub']), axis=1)
    # we only care about amount, timestamp, title and url
    df.drop(labels=['image', 'timestampms', 'titlesub'], axis=1, inplace=True)
    
    # finally, sort the sucker
    df = df.sort_values(['amount'], ascending=[True])

    if not args.dont_follow:
        follow_listings(df, args.wait, cache_dir)

    # outout to csv file        
    df.to_csv(output_file)
    print(f'Done: {output_file}')

if __name__ == "__main__":
    main()
