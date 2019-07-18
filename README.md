# Recommendation Engine

![](demo.GIF)

Using scraped data from Metacritic and IMDB, this model will take a TV Show as input and return 10 others that are recommended based on that show. Written in Python using mostly selectolax, scikit-learn, fuzzywuzzy, nltk, and pandas. 

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

Metacritic scores are based on the first season (this is why metascores carry a lower weight). In the future, we need to scrape data for the entire show or the average of all seasons.

## Setup

`metacritic_scraper.py` must run before `imdb_scraper`. Following this, the training and predicting can be done.

You can either run the main file in a terminal or run this as a flask webserver using `flask_api`.


