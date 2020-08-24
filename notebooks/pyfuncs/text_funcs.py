import string
import re
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import nltk
import pandas as pd

def remove_non_english_words(corpus):
    """Removes non english words by using nltk's words corpus. Captures most words."""
    words = set(nltk.corpus.words.words())
    clean_text = ([
    " ".join(w for w in nltk.wordpunct_tokenize(text)
    if w.lower() in words or not w.isalpha()) for text in corpus
     ])
    return clean_text

def cleaner(corpus, remove_non_english = False):
    '''Takes in a corpus (list) and returns cleaned text'''
    #remove punctuation
    clean_text = [text.translate(str.maketrans('', '', string.punctuation)) for text in corpus]
    #lowercase
    clean_text = [text.lower() for text in clean_text]
    #remove numbers
    clean_text = [re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", text) for text in clean_text]
    #removes words containing numbers
    clean_text = [re.sub("\S*\d\S*",'', text) for text in clean_text]
    if remove_non_english:
        clean_text = remove_non_english_words(clean_text)
    return clean_text

def count_vectorize(cleaned_corpus, min_doc_freq=0, max_doc_freq=1):
    """Takes in a corpus and returns document term matrix and tokenizer"""
    cv = CountVectorizer(stop_words='english', min_df=min_doc_freq, max_df=max_doc_freq)
    document_term_sparse_matrix = cv.fit_transform(cleaned_corpus)
    return pd.DataFrame(document_term_sparse_matrix.toarray(), columns=cv.get_feature_names()), cv

def tfidf_vectorize(cleaned_corpus, min_doc_freq=0, max_doc_freq=1):
    """returns Term Freq Inver Doc Freq Tokenization and tokenizer"""
    tfidf = TfidfVectorizer(stop_words='english', min_df=min_doc_freq, max_df=max_doc_freq)
    X_tfidf = tfidf.fit_transform(cleaned_corpus)
    return pd.DataFrame(X_tfidf.toarray(), columns = tfidf.get_feature_names()), tfidf

def get_pos_neg_neut(y, neutral_class=True):
    """Splits review_rating tarfet into positive,
     negative and netural class (if neutral_class=True)
     Returns y_new"""
    y_new = []
    y = [int(yi) for yi in y]
    if neutral_class==True:
        for yi in y:
            if yi < 3:
                #negative class
                y_new.append(-1)
            if yi > 3:
                #positive class
                y_new.append(1)
            if (yi == 3):
                #nuetral class
                y_new.append(0)
    else:
                for yi in y:
                    if yi <= 3:
                        #negative class
                        y_new.append(-1)
                    if yi > 3:
                        #positive class
                        y_new.append(1)
    return y_new
