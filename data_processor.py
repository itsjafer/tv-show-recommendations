# We will read from csv
# Convert the csv to a dataframe
# Clean up the 0s and treat them as missing values
# 

import pandas as pd
import numpy
from ast import literal_eval
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer # notice the spelling with the f before Vectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity

def load_tv_shows(path):
    df = pd.read_csv(path)
    return df


def inspect_data(df):
    info = pd.DataFrame(df.dtypes).T.rename(index={0:'column_type'})
    info = info.append(pd.DataFrame(df.astype(bool).sum()).T.rename(index={0:'valid values'}))
    return info


def count_word(df, ref_col, liste):
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
def create_soup(x):
    return ' '.join(x['keywords']) + ' '  + ' '.join(x['keywords']) + ' ' + 'seasons:' \
         + x['num_seasons'] + ' ' + x['runtime'] + ' ' + ' '.join(x['details']) + ' ' + \
             ' '.join(x['details']) + ' ' + ' '.join(x['cast']) + \
                 ' ' + x['user_rating_group'] + ' ' + ' '.join(x['synopsis'])

# Function to convert all strings to lower case and strip names of spaces
def clean_data(x):
    if isinstance(x, list):
        return [str.lower(i.replace(" ", "")) for i in x]
    else:
        if isinstance(x, str):
            return str.lower(x.replace(" ", ""))
        else:
            return ''

def get_similar(similarity_df, title):
    count = CountVectorizer(stop_words='english')
    tfidf = TfidfVectorizer()

    similarity_df['soup'] = similarity_df.apply(create_soup, axis = 1)

    tfidf_matrix = tfidf.fit_transform(similarity_df['soup'])
    count_matrix = count.fit_transform(similarity_df['soup'])

    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    cosine_sim2 = cosine_similarity(count_matrix, count_matrix)

    similarity_df = similarity_df.reset_index()
    indices = pd.Series(df.index, index=similarity_df['title'])

    # Get the index of the show that matches the title
    idx = indices[title]

    # Get the pairwsie similarity scores of all shows with that show
    sim_scores = list(enumerate(cosine_sim2[idx]))

    # Sort the shows based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the 50 most similar tv shows
    sim_scores = sim_scores[1:31]

    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores]

    # Return the top 30 most similar movies
    return similarity_df.iloc[movie_indices], sim_scores


def convert_rating_to_category(x):
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

# We load the csv into a dataframe
df = load_tv_shows('tv_shows_with_features.csv')

df_analysis = df
# Turn some columns into a list instead of str
list_columns = ['cast', 'details', 'keywords']
for column in list_columns:
    df_analysis[column] = df_analysis[column].apply(literal_eval)

df_analysis['synopsis'] = df_analysis['synopsis'].apply(lambda x: x.split(' '))

# Now we do some analysis
print('Analysis of Data:')
print('\nShape:', df_analysis.shape)
print()
print(inspect_data(df_analysis))

keywords = set()

for keywords_list in df_analysis['keywords']:
    keywords = keywords.union(keywords_list)

print('\nPrinting most popular keywords...\n')
keyword_occurences, count = count_word(df, 'keywords', keywords)
print(keyword_occurences[:10])
print()

print('Cleaning Data...\n')
features = ['cast','details','num_seasons','keywords','runtime', 'synopsis']
for feature in features:
    df_analysis[feature] = df_analysis[feature].apply(clean_data)

df_analysis['user_rating_group'] = df_analysis['user_rating'].apply(convert_rating_to_category)

title = 'Black Mirror'

print('Finding tv shows similar to ' + title + '...\n')
top_movies, sim_scores = get_similar(df_analysis, title)

# Add similarity scores

for i in sim_scores:
    top_movies.loc[i[0], 'similarity'] = i[1] * 100

top_movies['user_rating'] = top_movies['user_rating'] * 10
top_movies['score'] = top_movies['similarity'] * 0.2 + 0.8 * top_movies['user_rating']
top_movies = top_movies.sort_values('score', ascending=False)

print('Found the following TV Shows:\n')
print(top_movies[['title', 'score', 'user_rating', 'similarity']].head(10))
# Now we need to pick the 10 highest rated shows
