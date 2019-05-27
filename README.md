# TV Show Predictor

This is a simple pipeline that scrapes information from Metacritic and IMDB and uses cosine similarity on key features such as genre, plot, cast, production company, etc. and combines it with IMDB user rating to predict and recommend shows based on an input TV Show.

## Demo

You can see a demo of prediction on my [website](http://itsjafer.com/#/show-predictor).

## Overview

This pipeline uses BeautifulSoup to parse and scrape data off of Metacritic and IMDB. Then, we use pandas to create a dataframe from the scraped data. Finally, using nltk we create a 'soup' of useful features and find pairwise cosine similarity between all tv shows.

In terms of predicting, the web server runs through a Flask container. Given an input tv show, the model will find the 30 most similar tv shows based on features alone. Among those 30, a normalized user_rating and normalized similarity score is weighed at 75-25 to return the 10 most valuable recommendations.

## Setup

`metacritic_scraper.py` must run before `imdb_scraper`. Following this, the training and predicting can be done.

You can either run the main file in a terminal or run this as a flask webserver using `flask_api`.


