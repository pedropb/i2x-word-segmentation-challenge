#!/usr/bin/python

from __future__ import print_function
from __future__ import division
import sys, argparse, os
import dataset_tools
from utils import load_pickle, save_pickle, memoize
from collections import Counter
from functools import reduce 
import operator
from six.moves import range
from sgt import pdist_good_turing_hack as sgt
import re

P_BIGRAMS = {}
P_WORDS = {}

def count_words(text):
    """Count word occurences"""
    words = text.split(" ")
    return dict(Counter(words).most_common())

def count_bigrams(text):
    """Count bigram occurences"""
    words = text.split(" ")
    bigrams = [b for b in zip(words[:-1], words[1:])]
    return dict(Counter(bigrams).most_common())

def process_dict(text):
    """
    Process the dictionary and returns:
        - a occurence counter for every word in _text_.
        - a occurence counter for every bigram in _text_.

    Our dictionary is composed by the text8 dataset (http://mattmahoney.net/dc/textdata).

    This dataset contains the first 10^9 bytes of the English Wikipedia dump on Mar. 3, 2006.

    This dataset is cleaned and only contains lowercase characters from a to z, plus whitespaces.
    """

    BIGRAM_COUNT_PICKLE = "bigram_count.pickle"
    BIGRAM_COUNT = 4146849
    WORD_COUNT_PICKLE = "word_count.pickle"
    WORD_COUNT = 253855

    # Try to load previous word_count
    word_count = load_pickle(WORD_COUNT_PICKLE, WORD_COUNT)
    
    # if can't load pickle, then count words and save pickle
    if word_count == None:
        print("Pickle file not found. Counting words...")
        word_count = count_words(text)
        save_pickle(word_count, WORD_COUNT_PICKLE)

    # Try to load previous bigram_count
    bigram_count = load_pickle(BIGRAM_COUNT_PICKLE, BIGRAM_COUNT)

    # if can't load pickle, then count bigrams and save pickle
    if bigram_count == None:
        print("Pickle file not found. Counting bigrams...")
        bigram_count = count_bigrams(text)
        save_pickle(bigram_count, BIGRAM_COUNT_PICKLE)
    
    # making sure we have everything loaded correctly
    assert(type(word_count) == dict and type(bigram_count) == dict)

    return word_count, bigram_count

def prob(counter):
    """Probability of occurrence of each element from a counter."""
    corpus_size = sum(counter.values())
    return lambda el: float(counter[el]) / corpus_size

def prob_bigrams(words, prev='^', ):
    """Probability of occurrence of a sequence of words, using bigram counter."""
    return reduce(operator.mul,  
        (cond_prob(w, (prev if (i == 0) else words[i-1]) )
                   for (i, w) in enumerate(words)),
        initial=1)

def prob_words(words):
    """Probability of occurrence of words (assuming they are independent of each others)"""
    return reduce(operator.mul, [P_WORDS(w) for w in words], initial=1)

def cond_prob(word, prev):
    """Conditional probability of word given previous word."""
    
    bigram = (prev, word)
    if P_BIGRAMS(bigram) > 0 and P_WORDS(prev) > 0:
        return float(P_BIGRAMS(bigram)) / P_WORDS(prev)
    else: # non-zero probability
        return P_WORDS(word) / 2.0


@memoize
def segment_words(text, previous='^'):
    """
    Given a previous word, select the next word with the highest probability
    based on bigram counts.
    """ 
    if not text: 
        return []
    else:
        candidates = [[first] + segment_words(rest, first) 
                      for (first, rest) in split_text(text, 1)]

        return max(
            candidates, 
            key=lambda words: prob_bigrams(words, previous)
        )

def split_text(text, start=0, length=20):
    """
    Parses a string of text returning all combination of pairs
    with lengths varying from _start_ to _length_
    """
    end = min(len(text), length)
    return [(text[:i], text[i:]) for i in range(start, end+1)]

def mark_unknown_words(segmented_text, dictionary):
    """Transform words not present in the dictionary to uppercase."""
    result = segmented_text.upper()
    for word in dictionary:
        result = result.replace(word.strip().upper(), word.strip().lower())

    return result.strip()

def accuracy(text):
    """Returns the number of unrecognized characters"""
    return sum(1 for c in text if c.isupper())

def main(argv):
    # Configuring arguments    
    parser = argparse.ArgumentParser(
        description=(
            "Unconcatenate words from a string based on a given dictionary. Words not present on "
            "the dictionary will be written in UPPERCASE on the output and will count towards "
            "the number of unrecognized characters. Outputs: the unconcatenated string and the "
            "number of unrecongized characters." 
        )
    )

    parser.add_argument("concatenated_file", metavar="concatenated_file", type=str, 
        help="File containing the string with all words concatenated")

    parser.add_argument("-t", "--frequency-threshold", dest="frequency_threshold", type=float, default=0.001, 
        help=(
            "Frequency threshold (in %%) for considering words from the corpus dictionary (Default: 0.001)."
            " For example, words that appear on the corpus dictionary less than 0.001%% won't be used."
        ), required=False)

    # Parsing arguments
    args = parser.parse_args()

    # Print help and exit if there are not enough arguments
    if len(argv) < 1:
        parser.print_help()
        sys.exit(1)

    try:
        # Download DICT FILE
        dict_file = dataset_tools.maybe_download()

        # Checking if input files exist
        if not os.path.isfile(dict_file):
            print("Dictionary file missing: " + dict_file)
            return
        
        if not os.path.isfile(args.concatenated_file):
            print("Invalid argument: concatenated_file == " + args.concatenated_file)
            return
        
        # Reading files
        dict_file_text = dataset_tools.read_dict_file(dict_file)

        # Error handling
        if len(dict_file_text.strip()) == 0:
            print("dict_file is empty.")
        
        concatenated_file_text = ""
        with open(args.concatenated_file) as f:
            concatenated_file_text = f.read()

        concatenated_file_text = concatenated_file_text.lower()
        concatenated_file_text = re.sub("[^a-z ]", "", concatenated_file_text, )

        if len(concatenated_file_text.strip()) == 0:
            print("concatenated_file is empty.")
              
        print("Processing dictionary. This might take a while.")
        word_count, bigram_count = process_dict(dict_file_text)

        # Computing probability distributions
        print("Computing probability distributions...")
        global P_BIGRAMS
        global P_WORDS
        P_BIGRAMS = prob(bigram_count)
        P_WORDS = sgt(word_count)

        # Segmenting words from concatenated text
        print("Segmenting words...")
        segment_words.results.clear()
        segmented_text = segment_words(concatenated_file_text)
        segmented_text = ' '.join([w.strip() for w in segmented_text])
        segmented_text = mark_unknown_words(segmented_text, word_count.keys())

        # Final output
        print("Concatenated text:", concatenated_file_text)
        print("Segmented text:", ' '.join(segmented_text))
        print("Unrecognized characters: ", accuracy(segmented_text))

    except IOError as err:
        print(err.filename, err.message)
    except ValueError as err:
        print(err.message)
    except:
        raise
        print("Unexpected error")

if __name__ == "__main__":
    main(sys.argv[1:])