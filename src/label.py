import os
import pymongo
import sys

from bson.son import SON
from sortedcontainers import SortedDict

import pg_funcs

# create the connection
client = pymongo.MongoClient()
db = client.pgdb
    
# create the index on the doc_freqs collection
if "doc_freqs" not in db.list_collection_names():
    db.doc_freqs.create_index("bookid")

def read_stems(filepath):
    words = None
    try:
        with open(filepath, 'r') as f:
            words = f.read()
    except IOError:
        print('There was an issue reading in', filepath)
        raise IOError
    doc_freqs = SortedDict()
    for word in words.split(' '):
        if word not in doc_freqs:
            doc_freqs[word] = 1
        else:
            doc_freqs[word] += 1
    bookid = pg_funcs.extract_bookid(filepath)
    return bookid, doc_freqs

def insert_doc(bookid, doc_freqs):
    try:
        # dont add the book if it already exists
        if db.doc_freqs.count_documents({"bookid": {"$eq": bookid}}) > 0:
            return
        db.doc_freqs.insert_one({'bookid':bookid, 'terms':doc_freqs})
    except pymongo.errors.PyMongoError as e:
        print("Error:", e)
        client.close()
        sys.exit(-1)

def batch():
    '''
    Attempts to parse and upload ebook stems from stem files to MongoDB. 
    Makes no guarantees as to whether or not the files will be uploaded successfully.
    '''
    # check if the collection already exists, if so isue warning that we need to drop it since we are rebuiilding iit
    if db.docs_freqs.count_documents({}, hint="bookid") > 0:
        if input('Warning! Index already exists, do you want to rebuild it? [y|n]: ').lower() != 'y':
            return
        # drop the two index collections
        db.doc_freqs.drop()
        db.coll_freqs.drop()
    for filepath in pg_funcs.get_files(os.path.join('data', 'stems')):
        try:
            insert_doc(*read_stems(filepath))
        except IOError:
            continue
    # perform an aggregate on the doc_freqs collection to generate the collection frequency
    pipeline = [
        {"$project": {"terms": {"$objectToArray": "$terms"}}},
        {"$unwind": "$terms"},
        {"$group": {"_id": "$terms.k", "count": {"$sum": 1}}},
        {"$sort": SON([("_id", pymongo.ASCENDING), ("count", pymongo.DESCENDING)])},
        {"$out": "coll_freqs"}
    ]
    db.doc_freqs.aggregate(pipeline, allowDiskUse=True)
    
def single(filepath):
    '''
    Attempts to parse and insert a single stem file into MongoDB.
        filepath: The path to the stem file.
    '''
    try:
        bookid, doc_freqs = read_stems(filepath)
        insert_doc(bookid, doc_freqs)
    except IOError:
        client.close()
        sys.exit(-1)
    try:
        for term, _ in doc_freqs.items():
            # upsert on the term; note that MongoDB (actually WiredTiger) does not guarantee document level atomicity, this is dangerous and should really be checked
            # its okay in this case, since no one is simultaneously updating the database
            db.coll_freqs.update_one(filter={'_id': term}, update={'$inc': {'count': 1}}, upsert=True)
    except pymongo.errors.PyMongoError as e:
        print("Error:", e)

def usage(err=None):
    '''
    Prints usage information. Will also additionally print an error if one is passed.
    '''
    print('-'*80)
    print('Usage: python3 label.py [stemfile]')
    print('\tstemfile [optional]: filepath to a stem file to add to the database')
    print('Not passing a path to a stemfile will allow label.py to run in batch mode.')
    print('In batch mode, label.py attempts to parse stem files from the ./data/stems directory.')
    print('Also note that batch mode rebuilds the index! You will be asked for confirmation to rebuild it if it already exists.')
    print('-'*80)
    if err:
        print('Error:', err)
        print('-'*80)

def main():
    '''
    The psuedo-entry point of the program.
    '''
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg == '-h' or arg == '--help':
            usage()
            sys.exit(0)
        # operate in single file mode
        else:
            single(arg)
    # operate in batch mode
    else:
        batch()
    # close the connection
    client.close()

if __name__ == '__main__':
    main()
