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

from selectolax.parser import HTMLParser
from requests import get
from time import sleep,time
from random import randint
import os
import string
import warnings
import csv
import logging
from multiprocessing import Pool
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

if not os.path.exists("../logging"):
    os.makedirs("../logging")
if not os.path.exists("../data"):
    os.makedirs("../data")
logging.basicConfig(filename='../logging/imdb_scraper.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

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

columns = ('title', 'metascore', 'userscore', 'link', 'cast', 'details', 'num_seasons', 'user_rating', 'num_ratings', 'keywords', 'runtime', 'synopsis', 'plot')

# Returns the imdb page of a given show
def get_imdb_page(show):
    global requests

    logging.info("Scraping information for show: " + (show))
    # We want to query imdb one time
    url = 'https://www.imdb.com/search/title?title=' + show + '&title_type=tv_series,tv_miniseries&sort=popularity'
    # Making a response and parsing it
    response = get(url, headers=headers)

    if response.status_code != 200:
        logging.warning('Received status code, ' + str(response.status_code))
        raise Exception("Received a non-200 status code!")

    parser = HTMLParser(response.text)

    # Update progress bar and wait
    requests +=1
    elapsed_time = time() - start_time
    os.system('clear')
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))

    # We only care about the divs that have the movie name
    # imdb_page has the link to the tv show's imdb page
    if (len(parser.css(".lister-item-header a")) <= 0) :
        logging.warning('Did not find any results for: ' + show)
        raise Exception("Did not find a valif imdb page")
    imdb_page = "https://www.imdb.com" + parser.css_first(".lister-item-header a").attributes['href']

    return imdb_page


def get_features(show, imdb_page):
    global requests
    # Now we want to do the same thing as before and get features
    # Some code duplication here unfortunately
    response = get(imdb_page, headers=headers)
    if response.status_code != 200:
        logging.warning('Received status code, ' + str(response.status_code))
        raise Exception('Wrong status code!')

    parser = HTMLParser(response.text)

    # First, let's make sure this is a valid match
    # Remove punctuation and spaces
    translator = str.maketrans('', '', string.punctuation)
    title = str.lower(show[0].replace(" ", "")).translate(translator)
    foundTitle = str.lower(parser.css_first('.title_wrapper h1').text().strip().replace(" ", "")).translate(translator)
    # Check equality
    stringMatch = fuzz.ratio(title, foundTitle)
    logging.info("Match between " + title + " and " + foundTitle + " is " + str(stringMatch))
    if stringMatch < 80:
        logging.warning("Skipping show because we didn't find an exact match. Expected: " + show[0].strip() + \
             ". Got: " + parser.css_first('.title_wrapper h1').text().strip())
        raise Exception('Could not find an exact match for the show!')

    # Update progress bar and wait
    requests +=1
    elapsed_time = time() - start_time
    os.system('clear')
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))

    # Check if number of votes is valid
    if len(parser.css('[itemprop=ratingCount]')) <= 0:
        logging.warning("Skipping show because it doesn't have a rating")
        raise Exception('No rating for the show')

    num_ratings = float(parser.css_first('[itemprop=ratingCount]').text().replace(',' , '').strip())
    if num_ratings < 1000:
        logging.warning("Skipping show because it has " + str(num_ratings) + " < 1000 ratings")
        raise Exception('Not enough votes for this show')

    # Number of seasons
    if (len(parser.css('.seasons-and-year-nav')) <= 0):
        num_seasons = 0
    else:
        num_seasons = parser.css_first('.seasons-and-year-nav a').text()
    
    # User rating
    if (len(parser.css("[itemprop=ratingValue]")) <= 0):
        user_rating = 0
    else:
        user_rating = parser.css_first("[itemprop=ratingValue]").text()

    # Keywords
    keywords = list()
    # Parse main page for important keywords and genres
    for soup in parser.css('.see-more.inline.canwrap'):
        for word in soup.css('a'):
            if (word.text()[0:7] == 'See All'):
                continue
            keywords.append(word.text().strip().lower())

     # Episode length
    if len(parser.css('#titleDetails')) <= 0 or \
    len(parser.css_first('#titleDetails').css('time')) <= 0:
        length = 0
    else:
        length = parser.css_first('#titleDetails').css_first('time').text()

    # Miscellaneous details
    details = list()
    if len(parser.css('#titleDetails')) > 0:
        for soup in parser.css_first('#titleDetails').css('.txt-block'):
            if len(soup.css('a')) <= 0:
                continue
            detail = soup.css_first('a').text().strip()
            if (detail == "IMDbPro" or detail == 'See more'):
                continue
            details.append(soup.css_first('a').text().strip())
    
    cast = list()
    # Creator + Cast
    if len(parser.css('.credit_summary_item')) > 0:
        for soup in parser.css('.credit_summary_item'):
            for person in soup.css('a'):
                if (person.text()[:8] == 'See full'):
                    continue
                cast.append(person.text().strip())

    # Synopsis
    synopsis = str()
    if len(parser.css('#titleStoryLine')) <= 0 or \
        len(parser.css_first('#titleStoryLine').css('.inline.canwrap')) <= 0:
        synopsis = ' '
    else:
        synopsis = parser.css_first('#titleStoryLine').css_first('.inline.canwrap').css_first('span').text().strip()
    
    # Plot
    plot = str()
    if len(parser.css('.plot_summary')) <= 0 or \
    len(parser.css_first('.plot_summary').css('.summary_text')) <= 0:
        plot = ' '
    else:
        plot = parser.css_first('.plot_summary').css_first('.summary_text').text().strip()
        skipAfter = '...'
        plot = plot.split(skipAfter, 1)[0]

    # Now we need to make a row
    row = (show[0], show[1], show[2], imdb_page, cast, details, num_seasons, user_rating, num_ratings, keywords, length, synopsis, plot)

    return row


def scrape_data(show):
    try:
        imdb_page = get_imdb_page(show[0])
    except Exception as e:
        logging.warning('Could not get imdb page for show, ' + show[0])
        print(str(e))
        return
        
    try:
        row = get_features(show, imdb_page)
    except Exception as e:
        logging.warning('Could not get features for the show, ' + show[0])
        print(str(e))        
        return

    logging.info("Finished scraping, " + show[0] + ": " + str(row))

    tv_shows_with_features.append(row)

    with open('../data/tv_shows_with_features.csv', 'a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(row)
        logging.info("Wrote information to csv")


def get_info():

    with open('../data/tv_shows_with_features.csv', 'a') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(columns)

    # Get list of tv show names from csv
    with open("../data/tv.csv", 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        tv_shows = list(csv_reader)

    # Go through each tv show and get its information (we will parallelize this for speed)

    # Run this with a pool of 5 agents having a chunksize of 3 until finished
    agents = 4
    chunksize = 3

    with Pool(processes=agents) as pool:
        result = pool.map(scrape_data, tv_shows, chunksize)

    # Output the result
    print ('Result:  ' + str(result))

if __name__ == "__main__":
    get_info()


