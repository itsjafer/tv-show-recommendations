
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

class DataProcessor:

    def load_tv_shows(self, path):
        df = pd.read_csv(path)
        return df


    def inspect_data(self, df):
        info = pd.DataFrame(df.dtypes).T.rename(index={0:'column_type'})
        info = info.append(pd.DataFrame(df.astype(bool).sum()).T.rename(index={0:'valid values'}))
        return info


    def count_word(self, df, ref_col, liste):
        # This function was written by Fabien Daniel
        keyword_count = dict()
        for s in liste: keyword_count[s] = 0
        for liste_keywords in df[ref_col]:        
            if type(liste_keywords) == float and pd.isnull(liste_keywords): continue        
            for s in [s for s in liste_keywords if s in liste]: 
                if pd.notnull(s): keyword_count[s] += 1
        keyword_occurences = []
        for k,v in keyword_count.items():
            keyword_occurences.append([k,v])
        keyword_occurences.sort(key = lambda x:x[1], reverse = True)
        return keyword_occurences, keyword_count

    # We put an emphasis on keywords, cast, and details
    def create_soup(self, x):
        return ' '.join(x['keywords']) + ' '  + ' '.join(x['keywords']) + ' '  + ' '.join(x['keywords']) \
            + ' ' + 'seasons:' + x['num_seasons'] + ' ' + x['runtime'] + ' ' + ' '.join(x['details']) + \
            ' ' + ' '.join(x['details'])  + ' '.join(x['details'])  + ' '.join(x['details']) + ' ' + ' '.join(x['cast']) + ' ' + x['user_rating_group'] + \
            ' ' + ' '.join(x['plot']) + ' ' + ' '.join(x['synopsis'])

    # Function to convert all strings to lower case and strip names of spaces
    def clean_data(self, x):
        translator = str.maketrans('', '', string.punctuation)

        if isinstance(x, list):
            return [str.lower(i.replace(" ", "")).translate(translator) for i in x]
        else:
            if isinstance(x, str):
                return str.lower(x.replace(" ", "")).translate(translator)
            else:
                return ''


    def train_model(self, df_analysis):
        print('Created a vectorizer of all english words')
        count = CountVectorizer(stop_words='english')

        df_analysis['soup'] = df_analysis.apply(self.create_soup, axis = 1)

        count_matrix = count.fit_transform(df_analysis['soup'])

        cosine_sim = cosine_similarity(count_matrix, count_matrix)

        df_analysis['cosine_score'] = [i for i in cosine_sim]

        df_analysis = df_analysis.reset_index()

        return df_analysis

    def get_similar(self, df_analysis, title):
        
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

    def assign_score(self, top_shows, sim_scores):
        # Add similarity scores
        for i in sim_scores:
            top_shows.loc[i[0], 'similarity'] = i[1]

        # We're going to normalize the similarity and user_rating columns
        # Create a minimum and maximum processor object
        min_max_scaler = preprocessing.MinMaxScaler()

        # Normalize the data
        top_shows['user_rating_normal']=min_max_scaler.fit_transform(top_shows[['user_rating']])
        top_shows['similarity_normal']=min_max_scaler.fit_transform(top_shows[['similarity']])

        # Create a score using user rating and similarity
        top_shows['score'] = top_shows['similarity_normal'] * 0.25 + 0.75 * top_shows['user_rating_normal']
        top_shows = top_shows.sort_values('score', ascending=False)

        return top_shows.copy()

    def convert_rating_to_category(self, x):
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
        
        # We load the csv into a dataframe
        df = self.load_tv_shows('tv_shows_with_features.csv')

        df_analysis = df
        # Turn some columns into a list instead of str
        list_columns = ['cast', 'details', 'keywords']
        for column in list_columns:
            df_analysis[column] = df_analysis[column].apply(literal_eval)

        df_analysis['synopsis'] = df_analysis['synopsis'].apply(lambda x: x.split(' '))
        df_analysis['plot'] = df_analysis['plot'].apply(lambda x: x.split(' '))

        # Now we do some analysis
        print('Analysis of Data:')
        print('\nShape:', df_analysis.shape)
        print()
        print(self.inspect_data(df_analysis))

        keywords = set()

        for keywords_list in df_analysis['keywords']:
            keywords = keywords.union(keywords_list)

        print('\nPrinting most popular keywords...\n')
        keyword_occurences, count = self.count_word(df, 'keywords', keywords)
        print(keyword_occurences[:10])
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


