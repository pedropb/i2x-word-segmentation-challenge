import os, sys
from six.moves.urllib.request import urlretrieve
import zipfile

DICT_FILE_URL = 'http://mattmahoney.net/dc/'
DICT_FILE = "text8.zip"
DICT_FILE_SIZE = 31344016
last_percent_reported = None

def read_dict_file(filename=DICT_FILE):
    """Open zipfile read all data and return"""
    with zipfile.ZipFile(filename) as f:
        name = f.namelist()[0]
        data = f.read(name)
    return data

def download_progress_hook(count, blockSize, totalSize):
    """A hook to report the progress of a download. Reports every 5% change in download progress."""
    global last_percent_reported
    percent = int(count * blockSize * 100 / totalSize)

    if last_percent_reported != percent:
        if percent % 5 == 0:
            sys.stdout.write("%s%%" % percent)
            sys.stdout.flush()
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        
        last_percent_reported = percent

def maybe_download(filename=DICT_FILE, expected_bytes=DICT_FILE_SIZE):
    """Download a file if not present, and make sure it's the right size."""
    if not os.path.exists(filename):
        print("Downloading dictionary file")
        filename, _ = urlretrieve(DICT_FILE_URL + filename, filename, reporthook=download_progress_hook)
    statinfo = os.stat(filename)
    if statinfo.st_size == expected_bytes:
        print('Found and verified dictionary file')
    else:
        raise Exception(
        'Failed to verify ' + filename + '. Can you get to it with a browser?')
    
    return filename
