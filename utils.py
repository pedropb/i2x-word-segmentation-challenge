import os
from six.moves import cPickle as pickle

def memoize(f):
    """Memoize function to cache results from function f"""
    results = {}
    def helper(n):
        if n not in results:
            results[n] = f(n)
        return results[n]
    return helper

def load_pickle(filename, expected_size):
    """Load pickle file. Returns the object loaded or None if failed"""

    pickled_data = None
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as f:
                pickled_data = pickle.load(f)
            if len(pickled_data) != expected_size:
                os.remove(filename)
                pickled_data = None
        except:
            os.remove(filename)
            pickled_data = None

    return pickled_data

def save_pickle(obj, filename):
    """Serializes obj on filename"""
    with open(filename, 'w') as f:
        pickle.dump(obj, f)