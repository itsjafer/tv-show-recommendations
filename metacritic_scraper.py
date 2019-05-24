#   * We will scrape TV Show titles from metacritic (https://www.metacritic.com/browse/tv/title/all)
#   * Format of URL is https://www.metacritic.com/browse/tv/title/all/X?view=condensed&page=Y
#       where X = lowercase letter of alphabet, Y = page number from 0 to infinity
#   * For the sake of learning, we use BeautifulSoup to scrape

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

# We will look at first 5 pages of every letter in the alphabet
pages = [str(i) for i in range(0,5)]
alphabet = list(string.ascii_lowercase)

# We use this to keep track of time and requests
start_time = time()
requests = 0

# Create a list of tv show titles we will use
tv_show_titles = list()

for letter in alphabet:
    if requests > 5:
        break
    for page in pages:
        # Base URL
        url = 'https://www.metacritic.com/browse/tv/title/all/' + letter + '?view=condensed&page=' + page
        
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
        tv_show_containers = html_soup.find_all('div', {'class':'basic_stat product_title'})

        # If we're reached the end of the pages, go to the next letter
        if (len(tv_show_containers) == 0):
            break

        # Add the TV Shows
        for show in tv_show_containers:
            tv_show_titles.append(show.a.text.strip())

        # No more than 10 pages per letter
        if requests > 5:
            break

with open('tv_shows.csv', 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(tv_show_titles)