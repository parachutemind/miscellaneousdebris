import aiohttp
import requests
import sys
import tempfile
import os
import json
import time
import re
import datetime
import math
import pandas as pd

import plotly.graph_objs as go
import plotly.offline as po
import plotly.express as px

from plotly.subplots import make_subplots
from argparse import ArgumentParser 
from urllib import parse
from bs4 import BeautifulSoup

BAT_URL_ROOT = 'https://bringatrailer.com'
DEFAULT_WAIT_INTERVAL_SECS = 1

sort = {'a': 'amount', 'd': 'timestamp', 's': 'sold'}

# Miles matcher
#  E.g.,
#         '7,200 Kilometers (~4,500 Miles)'
#         '12k Miles'
#         '55,086 Kilometers (~34k Miles)'
#         '14,820 Miles'
#         '33k Indicated Miles'
#         '68k Kilometers Shown (~42k Miles)'
#         '7,200 Kilometers (~4,500 Miles)'
# unit test anybody? nah!
kmiles_matcher = re.compile("[0-9]+k \w*[ ]*miles", re.IGNORECASE)
miles_matcher = re.compile("[0-9,]+ \w*[ ]*miles", re.IGNORECASE)

CN_TRANS  = "transmission"
CN_VIN    = "VIN"
CN_LOC    = "location"
CN_YEAR   = "year"
CN_MILAGE = "milage"

def isHttpOk(status):
    return status == 200 or status == 304

def cache_response(file_name, content):
    try:
        with open(file_name, "w") as f:
            f.write(content)
    except IOError:
        return False

    return True

def parse_titlesub(titlesub):
    """
    quick and dirty way to know if a listing sold or not
    """
    return "Y" if (titlesub.lower().startswith("sold for")) else "N"

def parse_milage(milage):
    """
    Extract milage int from things like "25,000 Miles" or "24k Miles" strings
   
    """
    match = kmiles_matcher.search(milage)
    if match:
        val = int(''.join(filter(str.isdigit, match.group())))
        val *= 1000
    else:
        match = miles_matcher.search(milage)
        if match:
            val = int(''.join(filter(str.isdigit, match.group())))
        else:
            val = int(''.join(filter(str.isdigit, milage)))

    return val  


def plot_data(file, title, show_essentials=True):
    """
    Uses plotly to make pretty graphics and opens in a web browser: https://plot.ly/python/plot-data-from-csv/
    Defaults to color based on sold/not sold
    """
    csv = pd.read_csv(file)
    csv = csv.fillna(0)
    hover_data = []
    if show_essentials:
        hover_data = ['essentials']
    
    # Some good examples,
    # https://community.plot.ly/t/add-custom-legend-markers-color-to-plotly-python/19635/2
    # Conditional coloring of marker (not used here, but good for reference):
    #     marker=dict(
    #       color=(csv['sold'] == 'Y').astype('int'),
    #       colorscale=[[0, '#F7654E'], [1, '#068FF7']]
    #     )

    fig = make_subplots(rows=1, 
        cols=2,
        subplot_titles=("Price Over Time", "Price and Milage"))

    sold = csv.loc[csv.sold == 'Y']
    not_sold = csv.loc[csv.sold == 'N']

    # least square
    temp = px.scatter(csv, x=sold['timestamp'], y=sold['amount'], trendline='ols')
    trendline = temp.data[1]
    trendline.line = dict(color='firebrick')
    fig.add_trace(trendline,
        row=1, col=1
    )

    # locally weighted scatterplot smoothing
    temp = px.scatter(csv, x=sold['timestamp'], y=sold['amount'], trendline='lowess')
    trendline = temp.data[1]
    trendline.line = dict(color='#17becf')
    fig.add_trace(trendline,
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=sold['timestamp'], y=sold['amount'],
            mode="markers",
            marker=dict(
                color='#068FF7'
            ),
            showlegend=False,
            hoverinfo='text',
            hovertext=sold['essentials'],
            legendgroup='sold'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=not_sold['timestamp'], y=not_sold['amount'],
            mode="markers",
            marker=dict(
                color='#F7654E'
            ),
            showlegend=False,
            hoverinfo='text',
            hovertext=not_sold['essentials'],
            legendgroup='not-sold'
        ),
        row=1, col=1
    )
    
    #
    #  Milage and amount
    #
    fig.add_trace(
        go.Scatter(x=sold['milage'], y=sold['amount'],
            mode="markers",
            marker=dict(
                color='#068FF7'
            ),
            showlegend=False,
            hoverinfo='text',
            hovertext=sold['essentials'],
            legendgroup='sold'
        ),        
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=not_sold['milage'], y=not_sold['amount'],
            mode="markers",
            marker=dict(
                color='#F7654E'
            ),
            showlegend=False,
            hoverinfo='text',
            hovertext=not_sold['essentials'],
            legendgroup='not-sold'
        ),        
        row=1, col=2
    )

    # least squares linear approx: ols
    temp = px.scatter(csv, x=sold['milage'], y=sold['amount'], trendline='ols')
    trendline = temp.data[1]
    trendline.line = dict(color='firebrick')
    fig.add_trace(trendline,
        row=1, col=2
    )

    # locally weighted scatterplot smoothing
    temp = px.scatter(csv, x=sold['milage'], y=sold['amount'], trendline='lowess')
    trendline = temp.data[1]
    trendline.line = dict(color='#17becf')
    fig.add_trace(trendline,
        row=1, col=2
    )

    # trick to sync hidding sold/not-sold on both sub-plots
    fig.add_trace(
        go.Scatter(x=[None], y=[None], mode='markers',
            marker=dict(size=10, color='#068FF7'),
            legendgroup='sold', showlegend=True, name='Sold'))
    fig.add_trace(
        go.Scatter(x=[None], y=[None], mode='markers',
            marker=dict(size=10, color='#F7654E'),
            legendgroup='not-sold', showlegend=True, name='Not Sold'))

    # x-axis labels 
    fig.update_xaxes(title_text="Date", row=1, col=1, showspikes=True)
    fig.update_xaxes(title_text="Milage", row=1, col=2, showspikes=True)
            

    min_ts = csv['timestamp'].min()
    max_ts = csv['timestamp'].max()
    min_lt = time.localtime(min_ts)
    max_lt = time.localtime(max_ts)
    year_range = max_lt.tm_year - min_lt.tm_year
    step = math.ceil((max_ts - min_ts) / year_range)
    tsvals = [min_ts]
    tstext = [min_lt.tm_year]
    for interval in range(1, year_range+2):
        tsvals.append(min_ts + (step * interval))
        tstext.append(f"{min_lt.tm_year+interval}")

    fig.update_layout(
            xaxis = dict(
                tickmode = 'array',
                tickvals = tsvals,
                ticktext = tstext
            )
    )

    # y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1, showspikes=True)
    fig.update_yaxes(title_text="Price", row=1, col=2, showspikes=True)
    
    fig.update_layout(title_text=f'{title}', 
                      showlegend=True,
                      legend=make_legend())
    
    fig.show()

def make_legend():
    """
    Customize the legend style and position
    """
    return go.layout.Legend(
        traceorder="normal",
        bordercolor="Black",
        borderwidth=1
    )

def sanitize_essential_item(val, word_to_remove):
    """
    Helper to remove the word_to_remove and strip, whitespaces, newlines etc..
    """
    clean_re = re.compile(re.escape(word_to_remove), re.IGNORECASE)
    return clean_re.sub('', val).strip(' \t\n\r')

def get_listing_essentials(html_doc, row):
    """
    Get the BaT "listing essentials" from an auction page. This includes the mileage and mods that are included
    in the sidebar for each auction.
    Args:
        html_doc (str): BaT auction listing HTML doc
        row (obj): dataframe row with additional information

    Returns:
        dictionary with following fields: "essentials", "milage", "transmission", "loc", "VIN"
    """
    result = {}
    soup = BeautifulSoup(html_doc, "html.parser")
    essentials_div = soup.findAll("div", {"class": "listing-essentials"})
    # newline delimiter substitution so that plotly will render properly
    essentials_text = f"{row['title']}<br />{row['titlesub']}<br />"
    result['essentials'] = essentials_text + essentials_div[0].text.replace('\n', '<br />')
    
    # listing-essentials-item
    essentials_items = soup.findAll("li",{"class": "listing-essentials-item"})
    keys = [[CN_TRANS, CN_TRANS], ["chassis:", CN_VIN], ["location:", CN_LOC]]
    miles_found = False
    for item in essentials_items:
        val = item.text.lower()
        # milage is special
        if "miles" in val and not miles_found:
            miles_found = True # this guards against false positives further down items list.
            result[CN_MILAGE] = parse_milage(item.text)
        else:
            # other items can be generalized in a loop...
            for sk in keys:
                search_term = sk[0]
                key = sk[1]
                if search_term in val:
                    result[key] = sanitize_essential_item(item.text, search_term) 
    return result

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
    """
    Follow each auction listing and extract the "essentials" information from each page.

    WARNING: download is done serialy. It will take time! If you like coffee, this function
    is for you!
    TODO: drink less coffee and serialize the downloading of listing while being mindful not
    to hit BaT too hard.
    """
    # prep the data frame with the buckets for the information that will be extracted
    # from each auction listing.
    # df.insert(5, CN_YEAR, None) # TODO - this comes from the title of the results, not the lisiting.
    new_cols = [CN_MILAGE, CN_TRANS, CN_VIN, CN_LOC]
    start_index = 6
    for col in new_cols:
        df.insert(start_index, col, None)
        start_index += 1

    # put "essentials" always as the last column to keep the csv somewhat nicely formatted
    # for those using spreadsheet editors.
    df.insert(len(df.columns), 'essentials', None)
    for index, row in df.iterrows():
        url = row['url']
        res, html_doc = download_content(url, cache_dir)
        if isHttpOk(res):
            # extract information and add it to df.
            listing_info = get_listing_essentials(html_doc, row)
            df.loc[index, 'essentials'] = listing_info['essentials']
            for col in new_cols:
                if col in listing_info:
                    df.loc[index, col] = listing_info[col]
        else:
            # TODO count errors
            pass
        
        if res == 200:
            time.sleep(wait)

def main():
    parser = ArgumentParser(description='BaT price trend')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-u', type=str, dest='url', help="full url to page with information")
    action.add_argument('-p', type=str, dest='csv_file', help="only plot the provided csv file")
    parser.add_argument('-o', type=str, dest='output_file', help='(optional) output CSV file')
    parser.add_argument('-sort', type=str, dest='sort_type', help='(optional) sort by (a)mount(default), (d)ate, (s)old/not sold.')
    parser.add_argument('-results-only', action='store_true', help="(optional) don't parse listings")
    parser.add_argument('-force', action='store_true', dest='force_download', help="(optional) force download, don't use local cached files")
    parser.add_argument('-wait', type=int, default=DEFAULT_WAIT_INTERVAL_SECS, help=f'(optional) when following listings, wait specified seconds before hitting the next listing. Min and default is {DEFAULT_WAIT_INTERVAL_SECS}')

    args = parser.parse_args()
    if args.force_download:
        print("-f NYI")
        sys.exit(-1)

    if args.csv_file:
        # only plotting.
        plot_data(args.csv_file, title=args.csv_file, show_essentials=not args.results_only)
        sys.exit(0)

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
    category_title = soup.title.text.strip(' \t\n\r')
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
    df.insert(0, 'date', None)
    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # add the "sold" column based on the titlesub string
    df.insert(0, 'sold', None)
    df['sold'] = df.apply(lambda row: parse_titlesub(row['titlesub']), axis=1)

    # add the listing essentials for each listing
    if not args.results_only:
        follow_listings(df, args.wait, cache_dir)

    # we only care about amount, timestamp, title and url
    df.drop(labels=['image', 'timestampms', 'titlesub'], axis=1, inplace=True)
    
    # finally, sort the sucker
    if args.sort_type:
        df = df.sort_values([sort[args.sort_type]], ascending=[True])
    else:
        df = df.sort_values(['amount'], ascending=[True])

    # outout to csv file        
    df.to_csv(output_file)
    plot_data(output_file, title=category_title, show_essentials=not args.results_only)
    print(f'Done: {output_file}')


if __name__ == "__main__":
    main()
