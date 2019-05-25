# We will read titles from the csv and query IMDB for each
# We'll query imdb and then pick the first result (this is problematic)
# Then, we can get the following information:
#   * Number of seasons
#   * User rating
#   * Genres
#   * Release date
#   * Episode length
# We will take this information and create a dataframe

from bs4 import BeautifulSoup
from requests import get
from time import sleep,time
from random import randint
from IPython.core.display import clear_output
import string
import warnings
import csv

# Request header
headers = \
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

start_time = time()
requests = 0
tv_shows = list()
tv_shows_with_features = list()

# Get list of tv show names from csv
with open("tv_shows.csv", 'r') as f:
    csv_reader = csv.reader(f, delimiter=',')
    tv_shows = list(csv_reader)

flat_tv_shows = [item for sublist in tv_shows for item in sublist]

for show in flat_tv_shows:
    print(show)
    # We want to query imdb one time
    url = 'https://www.imdb.com/search/title?title=' + show + '&title_type=tv_series'
    # Making a response and parsing it
    response = get(url, headers=headers)

    if response.status_code != 200:
        warnings.warn('Received status code, ' + response.status_code)
        break

    html_soup = BeautifulSoup(response.text, 'html.parser')

    # Update progress bar and wait
    requests +=1
    sleep(randint(1,3))
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)

    # We only care about the divs that have the movie name
    # imdb_page has the link to the tv show's imdb page
    if (len(html_soup.find_all(class_='lister-item-header')) <= 0):
        continue
    imdb_page = "https://www.imdb.com" + html_soup.find(class_='lister-item-header').find('a').get('href')

    # Now we want to do the same thing as before and get features
    # Some code duplication here unfortunately
    response = get(imdb_page, headers=headers)
    if response.status_code != 200:
        warnings.warn('Received status code, ' + response.status_code)
        break

    html_soup = BeautifulSoup(response.text, 'html.parser')

    # Update progress bar and wait
    requests +=1
    sleep(randint(1,3))
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)

    # Now we need to parse features

    # Number of seasons
    if (len(html_soup.find_all(class_='seasons-and-year-nav')) <= 0):
        num_seasons = 0
    else:
        num_seasons = html_soup.find(class_='seasons-and-year-nav').find('a').text
    
    # User rating
    if (len(html_soup.find(itemprop='ratingValue')) <= 0):
        user_rating = 0
    else:
        user_rating = html_soup.find(itemprop='ratingValue').text

    # Keywords
    keywords = list()
    for soup in html_soup.find_all(class_='see-more inline canwrap'):
        for word in soup.find_all('a'):
            if (word.text[0:7] == 'See All'):
                continue
            keywords.append(word.text.strip().lower())

    # Episode length
    if len(html_soup.find_all(id='titleDetails')) <= 0 or \
    len(html_soup.find(id='titleDetails').find_all('time')) <= 0:
        length = 0
    else:
        length = html_soup.find(id='titleDetails').find('time').text
    
    # Now we need to make a row
    row = (show, num_seasons, user_rating, keywords, length)
    tv_shows_with_features.append(row)

    if requests > 15:
        break

print(tv_shows_with_features)
    

