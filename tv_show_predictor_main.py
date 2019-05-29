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
    os.remove("tv_shows.csv")

    # run metacritic scraper
    import metacritic_scraper

    # delete related csv file
    os.remove("tv_shows_with_features.csv")

    # run imdb scraper
    import imdb_scraper

    # remove saved model
    os.remove("cosine_model_old.pkl")
    os.rename("cosine_model.pkl", "cosine_model_old.pkl")

if __name__ == "__main__":

    result = input("Enter 'Y' if you want to scrape and retrain the model'. Enter anything else to continue.")
    if (result == 'Y'):
        scrape_data()

    if (not os.path.isfile('cosine_model.pkl')):
        print("No model found. Starting training process...")
        df_trained = show_data_processor.load_model()
    else:
        df_trained = show_data_processor.load_model()
        #df_trained = pickle.load(open('cosine_model.pkl', "rb"))

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
        top_shows = show_data_processor.assign_score(top_shows, sim_scores)
        top_shows = top_shows.set_index('index')
        

        print('Found the following TV Shows:\n')
        print(top_shows[['title', 'score', 'user_rating', 'similarity', 'metascore', 'userscore']].head(10))

        print('\nPlease enter the title of a TV Show')