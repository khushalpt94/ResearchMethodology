# -*- coding: utf-8 -*-
"""TextClassification_EHR.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1604PArBz_Rv8wHQufRL-9Wg-bKZIJjtX
"""

#importing the necessary libraries

import pandas as pd
import numpy as np
import scipy #used for mathematical functions

#import spacy and nltk libraries
import spacy
from spacy import displacy #display the entities
import nltk

#to use Python’s raw string notation for regular expression patterns
import re 

import nltk
nltk.download()

import pandas as pd
import numpy as np
import scipy

import spacy
from spacy import displacy
import nltk
import re

from nltk.corpus import stopwords
stopwords = stopwords.words('english')

from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import CountVectorizer
from sklearn import ensemble
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

np.random.seed(27)

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

plt.rcParams['figure.figsize'] = [20.0, 7.0]
plt.rcParams.update({'font.size': 22})

sns.set_palette('bright')
sns.set_style('white')
sns.set_context('talk', font_scale=0.8)

# read in the data
raw_data = pd.read_csv('/content/drive/My Drive/mtsamples_v2.csv')
raw_data.head()

#Clean, Normalize, and Pre-process Text
#Before attempting to apply any machine learning algorithms we must first pre-process our text. This step includes removing stop-words and unnecessary punctuations.

#Pre-processing techniques to try:

#tokenization
#tagging
#chunking
#lemmatization
# visualizing a sample text
sample_text = raw_data.iloc[0,4]
sample_text

# trying out potential tokenizers
# visualizing output with nltk default sentence tokenizer
nltk.sent_tokenize(text=sample_text)

# viewing output for RegExpTokenizer
SENTENCE_TOKENS_PATTERN = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!)\s'
regex_st = nltk.tokenize.RegexpTokenizer(
            pattern=SENTENCE_TOKENS_PATTERN,
            gaps=True)
regex_st.tokenize(sample_text)

# sentence tokenizer was not able to correctly tokenize the sentences. So applying some cleaning functions to see if we can get a better result.
def tokenize_text(text):
    sentences = nltk.sent_tokenize(text)
    word_tokens = [nltk.word_tokenize(sentence) for sentence in sentences] 
    return word_tokens

def remove_characters_before_tokenization(sentence, keep_dash=True):
    sentence = sentence.strip()
    if keep_dash:
        # removing most special characters
        # we want to keep at least - and / as these are important in this text
        PATTERN = r'[?|$|&|*|%|@|(|)|~|,|]'
        filtered_sentence = re.sub(PATTERN, r'', sentence)
        # replacing : with whitespace to ensure words don't run together
        filtered_sentence = re.sub(r'[:]', ' ', filtered_sentence)
        # adding whitespace after . to help tokenizer capture correct sentences
        filtered_sentence = re.sub(r'[.]', ' ', filtered_sentence)
    else:
        PATTERN = r'[^a-zA-Z0-9 ]'
        filtered_sentence = re.sub(PATTERN, r'', sentence)
    return filtered_sentence

# visualizing test output
cleaned_sample = remove_characters_before_tokenization(sample_text) 
cleaned_sample

nltk.sent_tokenize(text=cleaned_sample)

#With a little cleaning, the sentence tokenizer performed much better! Let's now modify our cleaning function from above. We should add functionality to remove stop words and further normalize the text by removing capitol letters.

#From viewing the sample text, I think the categories that are written in all caps may be an important feature, but lets go ahead and lowercase everything for now.

def normalize_text(doc):
    doc = doc.lower()
    # removing most special characters
    # we want to keep at least - and / as these are important in this text
    PATTERN = r'[?|$|&|*|%|@|(|)|~|,|]'
    doc = re.sub(PATTERN, r'', doc)
    # replacing : with whitespace to ensure words don't run together
    doc = re.sub(r'[:]', ' ', doc)
    # replacing . with whitespace to help tokenizer capture correct sentences
    doc = re.sub(r'[.]', ' ', doc)
    # removing extra whitespace
    doc = doc.replace('   ', ' ')
    doc = doc.strip()
    
    return doc

sample_normalized = normalize_text(sample_text)
sample_normalized

#Download Available pretrained statistical models for English
!python -m spacy download en_core_web_lg
!python -m spacy download en

# tokenize the transcriptions with spacy

nlp = spacy.load('en')
#nlp = spacy.load('en_core_web_lg')

def lemmatize_text(text):
    text = nlp(text)
    text = ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in text])
    return text

# lemmatizing corpus

lemma_sample = lemmatize_text(sample_normalized)
print(type(lemma_sample))
lemma_sample = nlp(lemma_sample)
print(type(lemma_sample))
lemma_sample

tokens = [token.text for token in lemma_sample if not token.is_stop]
tokens[0:10]

# using spacy to visualize a named entity annotated transcription
displacy.render(lemma_sample, style='ent', jupyter=True)

# visualizing the dependency tree for the first sentenece in our sample transcription

doc = nlp('subjective this 23-year - old white female present with complaint of allergy')
displacy.render(doc, style='dep', jupyter=True, options={'distance': 90})

# first checking our transcriptions for null values
raw_data.transcription.isnull().sum()

# dropping the 33 rows with no transcription text
df = raw_data.copy()
df.dropna(subset=['transcription'], inplace=True)

print('Transcriptions with null values:')
print(df.transcription.isnull().sum())

df.head()

# also dropping the unnnamed column as it doesnt provide any value
df.drop(columns=['Unnamed: 0'], axis=1, inplace=True)

normalize_corpus = np.vectorize(normalize_text)
df['transcriptions_normal'] = normalize_corpus(df.transcription)

df['lemma_transcription'] = [lemmatize_text(item) for item in df.transcriptions_normal]

df.head()

# loading nltk stopwords
stop_words = nltk.corpus.stopwords.words('english')

# from visual inspection of corpus adding to our stopword list
more_stops = ['aa', 'ab', 'abc', 'abcd', 'xxx', 'xyz', 'xii', 'dr', 'x', 'mg', 'p', 'ml']

stop_words = stop_words + more_stops
print (stop_words)

from nltk.tokenize.toktok import ToktokTokenizer
tokenizer = ToktokTokenizer()

# remove numbers and stopwords
def remove_stopwords_and_nums(text):
    tokens = tokenizer.tokenize(text)
    # remove all non-alpha characters
    tokens = filter(lambda x: x.isalpha(), tokens)
    tokens = [token.strip() for token in tokens]
    # filter out stopwords
    filtered_tokens = [token for token in tokens if token not in stop_words]
    filtered_text = ' '.join(filtered_tokens)
    return filtered_text

remove_stopwords_and_nums(lemma_sample)

df['alpha_only'] = [remove_stopwords_and_nums(item) for item in df.lemma_transcription]
df['alpha_tokens'] = [tokenizer.tokenize(text) for text in df.alpha_only]
df.sample(5)

# creating a list of the total vocabulary for the entire transcriptions corpus
# extend creates a flat list of words
total_vocab = []
for token in df.alpha_tokens:
    total_vocab.extend(token)

# removing duplicate words using set (unordered collection of distinct objects)
total_vocab = list(set(total_vocab))
total_vocab = pd.DataFrame({'words':total_vocab}, index=total_vocab)
total_vocab.sample(5)

from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(max_features=10000)
cv_matrix = cv.fit_transform(df.alpha_only)
cv_matrix = cv_matrix.toarray()
cv_matrix[0:10]

# get all unique words in corpus
vocab = cv.get_feature_names()
# show feature vectors
pd.DataFrame(cv_matrix, columns=vocab).head()

bv = CountVectorizer(ngram_range=(2,3), max_features=10000)
bv_matrix = bv.fit_transform(df.alpha_only)
bv_matrix = bv_matrix.toarray()

vocab = bv.get_feature_names()
pd.DataFrame(bv_matrix, columns=vocab).head()

# Commented out IPython magic to ensure Python compatibility.
from sklearn.feature_extraction.text import TfidfVectorizer

tv = TfidfVectorizer(max_features=10000,
                     min_df=2, #use only words appearing at least twice
                     max_df=0.7, #drop words occuring in a majority of the documents
                     stop_words='english',
                     ngram_range=(1,3)
                    )
# %time tv_matrix = tv.fit_transform(df.alpha_only)
tv_matrix = tv_matrix.toarray()

# vocabulary of features in tfidf matrix
vocab = tv.get_feature_names()
pd.DataFrame(np.round(tv_matrix, 2), columns=vocab).head()

from sklearn.metrics.pairwise import cosine_similarity

similarity_matrix = 1 - cosine_similarity(tv_matrix)
similarity_df = pd.DataFrame(similarity_matrix)
similarity_df.head()