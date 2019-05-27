from flask import Flask, jsonify, request
import os
from data_processor import DataProcessor
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle
from sys import stdin
import json

show_data_processor = DataProcessor()

if (not os.path.isfile('cosine_model.pkl')):
    print("No model found. Starting training process...")
    df_trained = show_data_processor.load_model()
else:
    df_trained = pickle.load(open('cosine_model.pkl', "rb"))
app = Flask(__name__)

@app.route('/predict', methods=['GET'])
def predict():
    title = request.args.get('title')

    # Find a tv show with the most similar title
    titles = df_trained['title'].tolist()
    similarTitle = process.extractOne(title, titles)[0]
    if (similarTitle != title):
        print('Found "' + similarTitle + '", which was the closest match\n')

    print('Finding tv shows similar to ' + similarTitle + '...\n')
    
    # Get a list of top 30 most similar shows
    top_movies, sim_scores = show_data_processor.get_similar(df_trained, similarTitle)

    # Normalize and assign a rating based on similarity, user_rating
    top_movies = show_data_processor.assign_score(top_movies, sim_scores)
    
    print('Found the following TV Shows:\n')
    prediction = top_movies[['title', 'score', 'user_rating', 'similarity']].head(10)
    return prediction.to_json(orient='index')

app.run(debug=True)

