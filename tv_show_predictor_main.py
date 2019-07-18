# This file is an interface to use the model to get recommendations.
# Run this file to get recommendations based on a tv show

import os
from data_processor import DataProcessor
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle
from sys import stdin
import logging

show_data_processor = DataProcessor()

def scrape_data():
    # delete any csv files that currently exist
    if (os.path.exists("data/tv.csv")):
        os.remove("data/tv.csv")

    if (os.path.exists("logging/metacritic_scraper.log")):
        os.remove("logging/metacritic_scraper.log")


    print('Scraping metacritic')
    # run metacritic scraper
    import metacritic_scraper

    # delete related csv file
    if (os.path.exists("data/tv_shows_with_features.csv")):
        os.remove("data/tv_shows_with_features.csv")

    # delete log files
    if (os.path.exists("logging/imdb_scraper.log")):
        os.remove("logging/imdb_scraper.log")    
        
    print('Scraping IMDB')
    # run imdb scraper
    get_info()

def manual_loop():
    result = input("Enter 'Y' if you want to scrape data")
    if result == 'Y':
        scrape_data()
        df_trained = show_data_processor.load_model()
    else:
        result = input("Enter 'Y' if you want to retrain the model.")
        if (result == 'Y'):
            # remove saved model
            if os.path.exists('data/cosine_model.pkl'):
                os.remove("data/cosine_model.pkl")
            df_trained = show_data_processor.load_model()
        else:
            df_trained = pickle.load(open('data/cosine_model.pkl', "rb"))

    print('Please enter the title of a TV Show')

    for title in stdin:

        # Find a tv show with the most similar title
        titles = df_trained['title'].tolist()

        similarTitle = process.extractOne(title, titles)[0]

        if (similarTitle != title):
            print('Found "' + similarTitle + '", which was the closest match\n')

        print('Finding tv shows similar to ' + similarTitle + '...\n')
        
        # Get a list of top 30 most similar shows
        top_shows, sim_scores = show_data_processor.get_similar(df_trained, similarTitle)

        # Normalize and assign a rating based on similarity, user_rating
        top_shows = show_data_processor.predict_score(top_shows, sim_scores)
        top_shows = top_shows.set_index('index')
        

        print('Found the following TV Shows:\n')
        print(top_shows[['title', 'score', 'user_rating', 'similarity', 'metascore', 'userscore']].head(15))

        print('\nPlease enter the title of a TV Show')

if __name__ == "__main__":
    manual_loop()
    # print('Scraping data')
    # scrape_data()
    # if (os.path.exists("data/cosine_model.pkl")):
    #     os.remove("data/cosine_model.pkl")
    # print('Training Model')
    df_trained = show_data_processor.load_model()