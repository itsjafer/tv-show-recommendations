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

from requests import get
from time import sleep,time
from random import randint
from IPython.core.display import clear_output
import string
import csv
import logging
from selectolax.parser import HTMLParser

logging.basicConfig(filename='imdb_scraper_fast.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
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

columns = ('title', 'metascore', 'userscore', 'link', 'cast', 'details', 'num_seasons', 'user_rating', 'num_ratings', 'keywords', 'runtime', 'synopsis', 'plot')
with open('tv_shows_with_features_fast.csv', 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(columns)

# Get list of tv show names from csv
with open("tv_shows.csv", 'r') as f:
    csv_reader = csv.reader(f, delimiter=',')
    tv_shows = list(csv_reader)

for show in tv_shows:
    logging.info("Scraping information for show: " + (show[0]))
    # We want to query imdb one time
    url = 'https://www.imdb.com/search/title?title=' + show[0] + '&title_type=tv_series'
    # Making a response and parsing it
    response = get(url, headers=headers)

    if response.status_code != 200:
        logging.warning('Received status code, ' + response.status_code)
        break

    #html_soup = BeautifulSoup(response.text, 'lxml')
    parser = HTMLParser(response.text)

    # Update progress bar and wait
    requests +=1
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)


    # We only care about the divs that have the movie name
    # imdb_page has the link to the tv show's imdb page
    if (len(parser.css(".lister-item-header a")) <= 0) :
        logging.warning('Did not find any results for: ' + show[0])
        continue
    imdb_page = "https://www.imdb.com" + parser.css_first(".lister-item-header a").attributes['href']
    
    # Now we want to do the same thing as before and get features
    # Some code duplication here unfortunately
    response = get(imdb_page, headers=headers)
    if response.status_code != 200:
        logging.warning('Received status code, ' + str(response.status_code))
        break

    #html_soup = BeautifulSoup(response.text, 'lxml')
    parser = HTMLParser(response.text)

    # First, let's make sure this is a valid match
    # Remove punctuation and spaces
    translator = str.maketrans('', '', string.punctuation)
    title = str.lower(show[0].replace(" ", "")).translate(translator)
    foundTitle = str.lower(parser.css_first('.title_wrapper h1').text().strip().replace(" ", "")).translate(translator)
    # Check equality
    if title != foundTitle:
        logging.warning("Skipping show because we didn't find an exact match. Expected: " + show[0].strip() + \
             ". Got: " + parser.css_first('.title_wrapper h1').text().strip())
        continue

    # Update progress bar and wait
    requests +=1
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)

    # Check if number of votes is valid
    if len(parser.css('[itemprop=ratingCount]')) <= 0:
        logging.warning("Skipping show because it doesn't have a rating")
        continue

    num_ratings = float(parser.css_first('[itemprop=ratingCount]').text().replace(',' , '').strip())
    if num_ratings < 1000:
        logging.warning("Skipping show because it has " + str(num_ratings) + " < 1000 ratings")
        continue

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
    # We will parse ALL the keywords
    skipAfter = '?ref'
    keyword_link = imdb_page.split(skipAfter, 1)[0] + 'keywords'

    response = get(keyword_link, headers=headers)
    requests +=1
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(requests, requests/elapsed_time))
    clear_output(wait = True)

    keyword_parser = HTMLParser(response.text)

    keywords = list()
    for word in keyword_parser.css('.sodatext'):
        keywords.append(word.text().strip())

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
    logging.info("Finished scraping, " + show[0] + ": " + str(row))
    with open('tv_shows_with_features_fast.csv', 'a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(row)
        logging.info("Wrote information to csv")

