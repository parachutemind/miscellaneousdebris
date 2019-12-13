import aiohttp
import requests
import sys
import tempfile
import os
import json
import pandas as pd
import plotly.express as px

from argparse import ArgumentParser 
from urllib import parse
from bs4 import BeautifulSoup

bat_url_root = 'https://bringatrailer.com'

sort = {'a': 'amount', 'd': 'timestamp', 's': 'sold'}


def cache_response(file_name, content):
    try:
        with open(file_name, "w") as f:
            f.write(content)
    except IOError:
        return False

    return True


def parse_titlesub(titlesub):
    return "Y" if (titlesub.lower().startswith("sold for")) else "N"


def plot_data(file):
    """
    Uses plotly to make pretty graphics and opens in a web browser: https://plot.ly/python/plot-data-from-csv/
    Defaults to color based on sold/not sold
    """
    csv = pd.read_csv(file)
    figure = px.scatter(csv, x='timestamp', y='amount', title="price over time",
                        hover_data=['essentials'], color="sold")
    figure.show()


def get_listing_essentials(url):
    """
    Get the BaT "listing essentials" from an auction URL. This includes the mileage and mods that are included
    in the sidebar for each auction.

    Warning: This can take a while to run on large csvs since it makes each web request in serial
    """
    print('Getting listing essentials for: {}'.format(url))
    doc = requests.get(url).text
    p_doc = BeautifulSoup(doc, "html.parser")
    essentials = p_doc.findAll("div", {"class": "listing-essentials"})
    # newline delimiter substitution so that plotly will render properly
    text = essentials[0].text.replace('\n', '<br />')
    return text


def main():
    parser = ArgumentParser(description='BaT price trend')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-f', type=str, dest='folder', help='name of folder in BaT or search term')
    action.add_argument('-u', type=str, dest='url', help="full url to page with information")
    parser.add_argument('-o', type=str, dest='output_file', help='(optional) output CSV file')
    parser.add_argument('-s', type=str, dest='sort_type',
                        help='(optional) sort by (a)mount(default), (d)ate, (s)old/not sold')

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
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d')

    # add the "sold" column based on the titlesub string
    df.insert(0, 'sold', None)
    df['sold'] = df.apply(lambda row: parse_titlesub(row['titlesub']), axis=1)

    # add the listing essentials for each listing to be displayed in the plot hover
    df.insert(0, 'essentials', None)
    df['essentials'] = df.apply(lambda row: get_listing_essentials(row['url']), axis=1)

    # we only care about amount, timestamp, title and url
    df.drop(labels=['image', 'timestampms', 'titlesub'], axis=1, inplace=True)
    
    # finally, sort the sucker
    if args.sort_type:
        df = df.sort_values([sort[args.sort_type]], ascending=[True])
    else:
        df = df.sort_values(['amount'], ascending=[True])

    # outout to csv file        
    df.to_csv(output_file)
    plot_data(output_file)
    print(f'Done: {output_file}')


if __name__ == "__main__":
    main()
