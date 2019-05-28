# Recommendation Engine

Using scraped data from Metacritic and IMDB, this model will take a TV Show as input and return 10 others that are recommended based on that show. Written in Python using mostly selectolax, scikit-learn, and pandas. 

## Model

The underlying model uses the following features (each weighted differently):

* Genres
* Plot
* Synopsis
* Cast
* Production company
* Keywords (describing the show)
* Number of seasons
* Episode runtime
* IMDB Rating
* Metacritic score
* Metacritic user score

Using these, the model finds pairwise cosine_similarities between every TV Show in the database. Combining the top 30 most similar with a weighted average of IMDB and metacritic scores gives an overall recommendation score.

## Demo

You can see a demo of prediction on my [website](http://itsjafer.com/#/show-predictor).

## Limitations

Titles are scraped from metacritic but feature data is scraped from imdb. This means there is (occasionally) a mismatch in titles and thus no data is collected. I'm planning to implement fuzzy matching to determine if the title is the same. However, there's a high risk of false positive matches (e.g. 'The Wire' with 'Wired')

## Setup

`metacritic_scraper.py` must run before `imdb_scraper`. Following this, the training and predicting can be done.

You can either run the main file in a terminal or run this as a flask webserver using `flask_api`.


