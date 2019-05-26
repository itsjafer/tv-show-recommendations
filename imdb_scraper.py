# We will read titles from the csv and query IMDB for each
# We'll query imdb and then pick the first result (this is problematic)
# Then, we can get the following information:
#   * Number of seasons
#   * User rating (+ number of ratings)
#   * Genres
#   * Release date
#   * Episode length
#   * Director and/or producer
#   * Cast
#   * Synopsis
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

columns = ('title', 'cast', 'details', 'num_seasons', 'user_rating', 'num_ratings', 'keywords', 'runtime', 'synopsis', 'plot')
with open('tv_shows_with_features.csv', 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(columns)

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

    # First, let's make sure this is a valid 
    if show != html_soup.find(class_='title_wrapper').find('h1').text.strip():
        print("Skipping show because we didn't find an exact match")
        continue

    # Update progress bar and wait
    requests +=1
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)

    # Now we need to parse features

    # Check if number of votes is valid
    if len(html_soup.find_all(itemprop='ratingCount')) <= 0:
        continue

    num_ratings = float(html_soup.find(itemprop='ratingCount').text.replace(',' , '').strip())
    if num_ratings < 1000:
        print("Skipping show because it has " + str(num_ratings) + " < 1000 ratings")
        continue

    # Number of seasons
    if (len(html_soup.find_all(class_='seasons-and-year-nav')) <= 0):
        num_seasons = 0
    else:
        num_seasons = html_soup.find(class_='seasons-and-year-nav').find('a').text
    
    # User rating
    if (len(html_soup.find_all(itemprop='ratingValue')) <= 0):
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

    # Miscellaneous details
    details = list()
    if len(html_soup.find_all(id='titleDetails')) > 0:
        for soup in html_soup.find(id='titleDetails').find_all(class_='txt-block'):
            if len(soup.find_all('a')) <= 0:
                continue
            detail = soup.find('a').text.strip()
            if (detail == "IMDbPro" or detail == 'See more'):
                continue
            details.append(soup.find('a').text.strip())
    
    cast = list()
    # Creator + Cast
    if len(html_soup.find_all(class_='credit_summary_item')) > 0:
        for soup in html_soup.find_all(class_='credit_summary_item'):
            for person in soup.find_all('a'):
                if (person.text[:8] == 'See full'):
                    continue
                cast.append(person.text.strip())

    # Synopsis
    synopsis = str()
    if len(html_soup.find_all(id='titleStoryLine')) <= 0 or \
        len(html_soup.find(id='titleStoryLine').find_all(class_='inline canwrap')) <= 0:
        synopsis = ' '
    else:
        synopsis = html_soup.find(id='titleStoryLine').find(class_='inline canwrap').find('span').text.strip()
    

    # Plot
    plot = str()
    if len(html_soup.find_all(class_='plot_summary')) <= 0 or \
    len(html_soup.find(class_='plot_summary').find_all(class_='summary_text')) <= 0:
        plot = ' '
    else:
        plot = html_soup.find(class_='plot_summary').find(class_='summary_text').text.strip()

    
    # Now we need to make a row
    row = (show, cast, details, num_seasons, user_rating, num_ratings, keywords, length, synopsis, plot)
        
    with open('tv_shows_with_features.csv', 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(row)
