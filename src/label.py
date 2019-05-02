import os
import pymongo
import sys

from bson.son import SON
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
    doc_freqs = SortedDict()
    for word in words.split(' '):
        if word not in doc_freqs:
            doc_freqs[word] = 1
        else:
            doc_freqs[word] += 1
    bookid = pg_funcs.extract_bookid(filepath)
    try:
        db.doc_freqs.insert_one({'bookid':bookid, 'terms':doc_freqs})
    except pymongo.errors.PyMongoError:
        print('There was an error connecting to MongoDB on localhost, unable to continue!')
        sys.exit(-1)
# perform an aggregate on the doc_freqs collection to generate the collection frequency
pipeline = [
    {"$project": {"terms": {"$objectToArray": "$terms"}}},
    {"$unwind": "$terms"},
    {"$group": {"_id": "$terms.k", "count": {"$sum": "$terms.v"}}},
    {"$sort": SON([("_id", 1), ("count", -1)])},
    {"$out": "coll_freqs"}
]
db.doc_freqs.aggregate(pipeline, allowDiskUse=True)
