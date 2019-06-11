
import pandas as pd
import os
from ast import literal_eval
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
from sklearn import preprocessing
import pickle
import numpy as np

class DataProcessor:

    def load_tv_shows(self, path):
        df = pd.read_csv(path)
        return df


    def inspect_data(self, df):
        info = pd.DataFrame(df.dtypes).T.rename(index={0:'column_type'})
        info = info.append(pd.DataFrame(df.astype(bool).sum()).T.rename(index={0:'valid values'}))
        return info

    # We put an emphasis on keywords, cast, and details
    def create_soup(self, x):
        """This function compiles all features of a row into a single column to be used to find similarities
        
        Arguments:
            x {DataFrame row} -- The row upon which to compile similarities
        
        Returns:
            String -- a space delimited string of features describing the row
        """
        keywords = x['keywords'] * 15
        details = x['details'] * 5
        cast = x['cast'] * 10
        return ' '.join(keywords) + ' ' + 'seasons:' + x['num_seasons'] + ' ' + x['runtime'] + ' ' + ' '.join(details) + \
            ' ' + ' '.join(cast) + ' ' + x['user_rating_group'] + ' ' + ' '.join(x['plot']) + ' ' + ' '.join(x['synopsis'])

    # Function to convert all strings to lower case and strip names of spaces
    def clean_data(self, x):
        """Converts a column into lowercase without spaces and no puncutation
        
        Arguments:
            x {List | String} -- The object to be cleaned
        
        Returns:
            List | String -- Cleaned object
        """
        translator = str.maketrans('', '', string.punctuation)

        if isinstance(x, list):
            return [str.lower(i.replace(" ", "")).translate(translator) for i in x]
        else:
            if isinstance(x, str):
                return str.lower(x.replace(" ", "")).translate(translator)
            else:
                return ''


    def train_model(self, df_analysis):
        """Finds pairwise cosine similarities between all TV Shows and saves it to a given DataFrame
        
        Arguments:
            df_analysis {DataFrame} -- The DataFrame of TV Shows to be trained on
        
        Returns:
            DataFrame -- The same DataFrame but with an added similarity column for each movie
        """
        print('Created a vectorizer of all english words')
        count = CountVectorizer(stop_words='english')

        df_analysis['soup'] = df_analysis.apply(self.create_soup, axis = 1)

        count_matrix = count.fit_transform(df_analysis['soup'])

        cosine_sim = cosine_similarity(count_matrix, count_matrix)

        df_analysis['cosine_score'] = [i for i in cosine_sim]

        df_analysis = df_analysis.reset_index()

        return df_analysis


    def get_similar(self, df_analysis, title):
        """Finds the most similar tv shows to a given tv show
        
        Arguments:
            df_analysis {DataFrame} -- The dataframe that is going to be used to find similarities
            title {String} -- The TV Show to find similar shows to
        
        Returns:
            DataFrame -- DataFrame with only rows of similar titles
            List -- A list of all the similarity scores of each title
        """
        indices = pd.Series(df_analysis.index, index=df_analysis['title'])

        # Get the index of the show that matches the title
        idx = indices[title]

        # Get the pairwsie similarity scores of all shows with that show
        sim_scores = list(enumerate(df_analysis['cosine_score'][idx]))

        # Sort the shows based on the similarity scores
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        # Get the scores of the 50 most similar tv shows
        sim_scores = sim_scores[1:51]

        # Get the movie indices
        show_indices = [i[0] for i in sim_scores]

        # Return the top 30 most similar movies
        return df_analysis.iloc[show_indices].copy(), sim_scores

    def predict_score(self, top_shows, sim_scores):
        """Predicts the recommendation score based on similarity and ratings
        
        Arguments:
            top_shows {DataFrame} -- The DataFrame with only rows related to the most similar TV Shows
            sim_scores {List} -- A list of all the similarity scores of each title
        
        Returns:
            DataFrame -- The same DataFrame but with an added score column
        """
        # Add similarity scores
        for i in sim_scores:
            top_shows.loc[i[0], 'similarity'] = i[1]

        # We're going to normalize the similarity and user_rating columns
        # Create a minimum and maximum processor object
        min_max_scaler = preprocessing.MinMaxScaler()

        # Normalize the data
        top_shows['user_rating_normal']=min_max_scaler.fit_transform(top_shows[['user_rating']])
        top_shows['similarity_normal']=min_max_scaler.fit_transform(top_shows[['similarity']])
        top_shows['metascore_normal']=min_max_scaler.fit_transform(top_shows[['metascore']])
        top_shows['userscore_normal']=min_max_scaler.fit_transform(top_shows[['userscore']])

        # Create a score using user rating and similarity
        top_shows['score'] = top_shows['similarity_normal'] * 0.20 + 0.35 * top_shows['user_rating_normal'] + 0.37 * top_shows['userscore_normal'] + 0.08 * top_shows['metascore_normal']
        top_shows = top_shows.sort_values('score', ascending=False)

        return top_shows.copy()


    def convert_rating_to_category(self, x):
        """Convert rating levels to a category for easy use in soups
        
        Arguments:
            x {Integer} -- The rating of a TV Show
        
        Returns:
            String -- description of the rating in words
        """
        rating = x
        result = str()
        if rating > 9:
            result = "masterpiece"
        elif rating > 8:
            result = "great"
        elif rating > 7:
            result = "good"
        elif rating > 6:
            result = "mediocre"
        else:
            result = "bad"
        return result


    def load_model(self):
        """Loads the model from a csv into a DataFrame and does some basic cleaning, analysis, and training
        
        Returns:
            DataFrame -- Trained model based on the data used
        """
        # We load the csv into a dataframe
        df = self.load_tv_shows('data/tv_shows_with_features.csv')

        df_analysis = df
        # Turn some columns into a list instead of str
        list_columns = ['cast', 'details', 'keywords']
        for column in list_columns:
            df_analysis[column] = df_analysis[column].apply(literal_eval)

        df_analysis['synopsis'] = df_analysis['synopsis'].apply(lambda x: x.split(' '))
        df_analysis['plot'] = df_analysis['plot'].apply(lambda x: x.split(' '))

        # Fill in missing metascore values with the related imdb and userscore
        df_analysis['metascore'] = np.where(df['metascore'] == 0, df['user_rating'], df['metascore'])

        # Fill in missing userscore values with the related imdb and metascore
        df_analysis['userscore'] = np.where(df['userscore'] == 0, df['user_rating'], df['userscore'])
        df_analysis['userscore'] = np.where(df['userscore'] == 0, df['metascore'], df['userscore'])

        # Now we do some analysis
        print('Analysis of Data:')
        print('\nShape:', df_analysis.shape)
        print()
        print(self.inspect_data(df_analysis))
        print()

        print('Cleaning Data...\n')
        features = ['cast','details','num_seasons','keywords','runtime', 'synopsis']
        for feature in features:
            df_analysis[feature] = df_analysis[feature].apply(self.clean_data)

        df_analysis['user_rating_group'] = df_analysis['user_rating'].apply(self.convert_rating_to_category)

        print('Training Model...\n')

        df_trained = self.train_model(df_analysis)

        print('Trained!')

        pickle.dump(df_trained, open('cosine_model.pkl', "wb"))

        print('Saved model as cosine_model.pkl')

        return df_trained


