import logging
logging.basicConfig(filename='logging/web_server.log', filemode='w', format='%(asctime)s: %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

# This file is a flask API that enables use of the model's
# recommendations through other websites.

from flask import Flask, jsonify, request
from flask_cors import CORS
from tv_show_predictor_main import scrape_data

import os
from data_processor import DataProcessor
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle
from sys import stdin
import json

show_data_processor = DataProcessor()
app = Flask(__name__)
cors = CORS(app, resources={r"/predict": {"origins": "*"}})
if (os.path.exists("data/cosine_model.pkl")):
    os.remove("data/cosine_model.pkl")
print('Training Model')
df_trained = show_data_processor.load_model()

@app.route('/predict', methods=['GET'])
def predict():
    title = request.args.get('title')
    logging.info("Recieved request for title, " + title)
    # Find a tv show with the most similar title
    titles = df_trained['title'].tolist()
    similarTitle = process.extractOne(title, titles)[0]
    if (similarTitle != title):
        logging.info('Found "' + similarTitle + '", which was the closest match\n')

    logging.info('Finding tv shows similar to ' + similarTitle + '...\n')
    
    # Get a list of top 30 most similar shows
    top_shows, sim_scores = show_data_processor.get_similar(df_trained, similarTitle)

    # Normalize and assign a rating based on similarity, user_rating
    top_shows = show_data_processor.predict_score(top_shows, sim_scores)
    top_shows = top_shows.set_index('index')
    top_shows['similarTitle'] = similarTitle

    logging.info('Found the following TV Shows:\n')
    prediction = (top_shows.head(15).to_json(orient='records'))
    logging.info(top_shows.head(10))

    return prediction

if __name__ == '__main__':
    app.run(debug=True)