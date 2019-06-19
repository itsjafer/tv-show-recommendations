#   * We will scrape TV Show titles from metacritic (https://www.metacritic.com/browse/tv/title/all)
#   * Format of URL is https://www.metacritic.com/browse/tv/title/all/X?view=condensed&page=Y
#       where X = lowercase letter of alphabet, Y = page number from 0 to infinity
#   * For the sake of learning, we use BeautifulSoup to scrape

from bs4 import BeautifulSoup
from requests import get
from time import sleep,time
from random import randint
import string
import warnings
import csv
import logging
import os

if not os.path.exists("logging"):
    os.makedirs("logging")
logging.basicConfig(filename='logging/metacritic_scraper.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

# Request header
headers = \
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

# We will look at first 100 pages of every letter in the alphabet
pages = [str(i) for i in range(0,100)]
alphabet = list(string.ascii_lowercase)
alphabet.append('#')
file_names = ('tv',)

for name in file_names:

    # We use this to keep track of time and requests
    start_time = time()
    requests = 0
    row = ('title', 'metascore', 'userscore')
    with open('data/' + name + '.csv', 'a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(row)

    tv_shows = list()

    for letter in alphabet:
        logging.info("Looking at all shows that start with: " + letter)
        for page in pages:
            logging.info("Looking at page " + page)
            # Base URL
            url = 'https://www.metacritic.com/browse/' + name + '/title/all/' + letter + '?view=condensed&page=' + page
            print(url)
            # Making a response and parsing it
            response = get(url, headers=headers)

            if response.status_code != 200:
                warnings.warn('Received status code, ' + str(response.status_code))
                break

            html_soup = BeautifulSoup(response.text, 'html.parser')

            # Update progress bar and wait
            requests +=1
            elapsed_time = time() - start_time
            os.system('clear')
            print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))

            # We only care about the divs that have the movie name
            tv_show_containers = html_soup.find_all('div', {'class':'product_wrap'})

            # If we're reached the end of the pages, go to the next letter
            if (len(tv_show_containers) == 0):
                logging.info("No more results found on page " + page)
                break

            # Add the TV Shows
            for show in tv_show_containers:

                # We need to get the name of the show
                title = show.find(class_="basic_stat product_title").a.text.strip()
                if (title.split(':')[-1].strip() == 'Season 1'):
                    title = title[:-10]

                # Now let's get the metascore
                metascore = show.find(class_='brief_metascore').find(class_='metascore_w').text.strip()
                if (metascore == 'tbd'):
                    logging.warning("The show, " + title + " has no metascore. Setting to 0.")
                    metascore = 0
                
                # Finally, user score
                userscore = show.find(class_='product_avguserscore').find(class_='textscore').text.strip()
                if (userscore == 'tbd'):
                    logging.warning("The show, " + title + " has no userscore so we set it to 0.")
                    userscore = 0

                row = (title, metascore, userscore)
                tv_shows.append(row)    
            if letter == '#':
                break

    with open('data/' + name + '.csv', 'a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(tv_shows)
        logging.info("Wrote all rows to " + name + ".csv")