import os
import pymongo
import sys

from sortedcontainers import SortedDict

import pg_funcs

client = pymongo.MongoClient()
db = client.pgdb
for filepath in pg_funcs.get_files(os.path.join('data', 'stems')):
    words = None
    try:
        with open(filepath, 'r') as f:
            words = f.read()
    except IOError:
        print('There was an issue reading in', filepath)
        print('The file was not processed into MongoDB!')
    freq = SortedDict()
    for word in words.split(' '):
        if word not in freq:
            freq[word] = 1
        else:
            freq[word] += 1
    bookid = pg_funcs.extract_bookid(filepath)
    try:
        db.freqs.insert_one({'bookid':bookid, 'terms':freq})
    except pymongo.errors.PyMongoError:
        print('There was an error connecting to MongoDB on localhost, unable to continue!')
        sys.exit(-1)
