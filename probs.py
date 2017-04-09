from __future__ import division
from functools import reduce 
import operator

def prob(counter):
    """Probability of occurrence of each element from a counter."""
    corpus_size = sum(counter.values())
    return lambda el: float(counter[el]) / corpus_size

def prob_bigrams(words, prev='^', ):
    """Probability of occurrence of a sequence of words, using bigram counter."""
    return reduce(operator.mul,  
        (cond_prob(w,
            (prev if (i == 0) else words[i-1] for (i, w) in enumerate(words)))),
        initial=1)

def prob_words(words):
    """Probability of occurrence of words (assuming they are independent of each others)"""
    global P_WORDS
    return reduce(operator.mul, [P_WORDS(w) for w in words], initial=1)

def cond_prob(word, prev):
    """Conditional probability of word given previous word."""
    
    global P_BIGRAMS
    global P_WORDS
    
    bigram = (prev, word)
    if P_BIGRAMS(bigram) > 0 and P_WORDS(prev) > 0:
        return float(P_BIGRAMS(bigram)) / P_WORDS(prev)
    else: # non-zero probability
        return P_WORDS(word) / 2.0
