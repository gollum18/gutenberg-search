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
    return filename, completed.stdout.decode('utf-8')

# Used to convert a month string to it's corresponding numerical 
#   representation
months = {'january': '01', 'february': '02', 'march': '03', 
        'april': '04', 'may': '05', 'june': '06', 
        'july': '07', 'august': '08', 'september': '09', 
        'october': '10', 'november': '11', 'december': '12'}

'''
Dates in Gutenberg eBooks have a regular format, unfortunately, the eBook
number is listed alongside it. This method takes the date string, gets 
rid of the eBook number part, and converts the string to the following 
standard format 'DD/MM/YYYY' then returns it.
Sometimes the day is not specified, in this case the string that is 
returned is in the form --/MM/YYYY.
'''
def convert_date(date_str):
    date_str = date_str.lower()
    #strip off the key
    date_str = date_str.replace('release date: ', '')
    # get the left half of the ebook number where the date is
    if 'ebook' in date_str:
        date_str = date_str.split('[ebook')[0]
    # get the separate parts of the date
    parts = date_str.split(' ')
    parts = [x for x in parts if x != '']
    date = ''
    if len(parts) == 2:
        # return the string without the day
        return '--/{0}/{1}'.format(months[parts[0].split(',')[0]], parts[1])
    else:
        # return the standard formatted string
        return '{1}/{0}/{2}'.format(months[parts[0]], 
            parts[1].split(',')[0].zfill(2), parts[2])

'''
This method takes a key (which is a string) and a line (another string) and outputs the corresponding value to the key.
'''
def get_value(key, line):
    if key == keys['release_date']:
        return convert_date(line.rstrip('\n'))
    return line.split(key)[1].rstrip('\n')

# These keys are format specific. If the format used by Project Gutenberg
#   ever changes, then these keys will need to change with it
keys = {'title':'Title: ', 'author':'Author: ', 'release_date':'Release Date: ', 'language':'Language: ', 'char_set':'Character set encoding: ', 'publisher':'Produced by '}

# custom alphabet used during stemming to prune out bad characters
good_alphabet = string.ascii_lowercase + '-' + ' ' + '.' + '/' + ':'

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
def get_book(content):
    from io import StringIO
    from stemming import porter2
    text = content[1]
    book = dict()
    parts = content[0].split('/')
    book['bookid'] = parts[len(parts)-1].rstrip('.txt')
    for key, _ in keys.items():
        book[key] = ''
    book['filepath'] = content[0]
    book['stemmings'] = ''
    with StringIO(text) as content:
        for line in content:
            # TODO: Need to come up with a way to get keys that are broken
            #   across multiple lines
            for key, value in keys.items():
                if line.startswith(value):
                    book[key] = get_value(value, line)
                    break
            # stem the words in the line one at a time
            #   strip everything thats not a letter, digit, a hyphen, or a
            #   space
            line = ''.join(c for c in line.lower() if c in good_alphabet)
            for word in line.split(' '):
                # strip off all characters we dont want
                word = word.strip(string.punctuation)
                # skip stop words
                if word in stop_words or '/' in word or word.isspace() or word == '':
                    continue
                # dont index hyphens
                if word == '-':
                    continue
                # skip words that begin or end with periods
                if word.startswith('.') or word.endswith('.'):
                    continue
                # stem the remaining words
                book['stemmings'] = ' '.join([book['stemmings'], porter2.stem(word)])
    book['stemmings'] = book['stemmings'].lstrip(' ')
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
    stems = db.stems
    for r, dirs, _ in os.walk(os.path.join('data', 'aleph.gutenberg.org', folder)):
        for d in dirs:
            files = [os.path.join(r, d, f) for f in os.listdir(os.path.join(r, d)) if f.endswith('.txt')]
            for book in map(get_book, map(convert, files)):
                #books.insert_one({k:v for k, v in book.items() if k != 'stemmings'})
                #stems.insert_one({'bookid':book['bookid'], 'stemmings':book['stemmings']})
                pass

'''
The main method.
'''
def main():
    for i in range(1, 10):
        process_folder(str(i))

if __name__ == '__main__':
    main()
