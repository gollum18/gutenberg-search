import os
import string
import sys

# read in the stop words from file
stop_words = []
try:
    with open('stop.txt', 'r') as f:
        for word in f:
            stop_words.append(word)
except IOError:
    print('Error: Cannot process eBooks, there was an issue reading stop.txt!')
    sys.exit(1)

'''
This method uses the GNU `strings` program to attempt to convert a file of 
variable encoding to a UTF-8 format.
'''
def convert(filename):
    import subprocess
    # note that this is likely the slow part of the program
    completed = subprocess.run(args=['strings', filename], stdout=subprocess.PIPE)
    return completed.stdout.decode('utf-8')

'''
This method takes a key (which is a string) and a line (another string) and outputs the corresponding value to the key.
'''
def get_value(key, line):
    return line.split(key)[1]

# These keys are format specific. If the format used by Project Gutenberg
#   ever changes, then these keys will need to change with it
keys = {'title':'Title: ', 'author':'Author: ', 'release_date':'Release Date: ', 'language':'Language: ', 'char_set':'Character set encoding: ', 'publisher':'Produced by '}

# custome alphabet used during stemming to prune out bad characters
good_alphabet = string.ascii_lowercase + string.digits + '-' + ' ' + '.' + '/' + ':'

'''
Given the text of a book, extract out a map with the following information:
    bookid: The official Project Gutenberg bookid.
    title: The title of the book.
    author: The author of the book.
    release_date: The release date of the book on Project Gutenberg.
    language: The language of the book.
    char_set: The character set (supposedly) used to encode the book.
    publisher: The publisher of the book.
    stemmings: The text of the book with all stop words and most whitespace removed, as well as all of the remaining words stemmed and delineated by spaces.
'''
def get_book(text):
    from io import StringIO
    from stemming import porter2
    book = dict()
    book['bookid'] = ''
    for key, _ in keys.items():
        book[key] = ''
    book['stemmings'] = []
    # used when a key value could be split over multiple lines
    last_key = None
    with StringIO(text) as content:
        for line in content:
            if last_key and not line.isspace():
                book[last_key] += book[last_key] + line
            # reset the key when we get to a line that is whitespace
            elif line.isspace():
                last_key = None
            # otherwise proceed to the normal case
            else:
                for key, value in keys.items():
                    if line.startswith(value):
                        book[key] = get_value(value, line)
                        lastKey = key
                        break
            # stem the words in the line one at a time
            #   strip everything thats not a letter, digit, a hyphen, or a
            #   space
            line = ''.join(c for c in line.lower() if c in good_alphabet)
            for word in line.split(' '):
                # skip stop words
                if word in stop_words or word == '' or word.contains('/'):
                    continue
                # skip uris
                if word.contains('/'):
                    continue
                # stem the remaining words
                book['stemmings'].append(porter2.stem(word))
    return book

'''
Used to process a folder containing eBooks. eBooks are transformed into a 
map compatible with MongoDB then written to the pgb.books collection on 
localhost.
'''
def process_folder(folder):
    from pymongo import MongoClient
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
                book['filepath'] = f
                books.insert_one(book)

'''
The main method.
'''
def main():
    from multiprocessing import Process
    for i in range(1, 10):
        p = Process(target=process_folder, args=(str(i)))
        p.start()
        p.join()

if __name__ == '__main__':
    main()
