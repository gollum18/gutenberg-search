import os
import subprocess
from subprocess import PIPE

def convert(filename):
    completed = subprocess.run(args=['strings', filename], stdout=PIPE)
    return completed.stdout.decode('utf-8')

def get_value(key, line):
    return line.split(key)[1]

from io import StringIO

keys = {'title':'Title: ', 'author':'Author: ', 'release_date':'Release Date: ', 
        'language':'Language: ', 'char_set':'Character set encoding: ', 'publisher':'Produced by '}

def get_book(text):
    book = dict()
    book['bookid'] = ''
    for key, _ in keys.items():
        book[key] = ''
    book['text'] = ''
    last_key = None
    with StringIO(text) as content:
        for line in content:
            if last_key and not line.isspace():
                book[last_key] += book[last_key] + line
            elif line.isspace():
                last_key = None
            else:
                for key, value in keys.items():
                    if line.startswith(value):
                        book[key] = get_value(value, line)
                        lastKey = key
                        break
            book['text'] += line
    return book

import json
from multiprocessing import Process
from pymongo import MongoClient

def process_folder(folder):
    client = MongoClient('mongodb://localhost:27017')
    db = client.pgb
    books = db.books
    for r, dirs, _ in os.walk(os.path.join('data', 'aleph.gutenberg.org', folder)):
        for d in dirs:
            files = [os.path.join(r, d, f) for f in os.listdir(os.path.join(r, d)) if f.endswith('.txt')]
            for f in files:
                book = get_book(convert(f))
                id_str = f.split('.txt')[0]
                id_parts = id_str.split(os.path.sep)
                book['bookid'] = id_parts[len(id_parts)-1]
                books.insert_one(book)

for i in range(1, 10):
    p = Process(target=process_folder, args=(str(i)))
    p.start()
    p.join()
