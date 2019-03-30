# Name: convert.py
# Since: 24/03/2019
# Author: Christen Ford
# Description: Converts eBook text files from the Gutenberg Project into JSON strings, then uploads them into a MongoDB connection.

import chardet
import pymongo
import os
import stemming.porter2 as stemmer
import string
import sys

from io import StringIO

# stores text->key mappings, where key is the key in the
#   ebook dictionary and text is the way the key appears in the 
#   ebook files
key_map = {'Title: ':'title', 'Author: ':'author', 'Release Date: ':'release_date', 'Language: ':'language', 'Character set encoding: ':'char_set', 'Produced by ':'publisher'}

def extract_date(release_date):
    parts = release_date.split('[EBook')
    parts = parts[0].split(' ')
    if len(parts) == 4:
        month = parts[0].lower()
        day = parts[1].replace(',', '')
        year = parts[2]
        return month, day, year
    else:
        month = parts[0].replace(',', '').lower()
        year = parts[1]
        return month, None, year

def extract_value(key, line):
    return line.replace(key, '').replace('\r\n', '')

def get_bookid(filepath):
    parts = filepath.split(os.sep)
    return parts[len(parts)-1].replace('.txt', '')

alphabet = string.ascii_lowercase + string.digits + " " + "'"

def get_ebook(filepath):
    rawdata = None
    with open(filepath, 'rb') as f:
        rawdata = f.read()
    if chardet.detect(rawdata)['encoding'] == 'ascii':
        rawdata = str(rawdata, 'ascii').replace('\\r\\n', os.sep)
    else:
        rawdata = str(rawdata, 'iso-8859-1').replace('\\r\\n', os.sep)
    ebook = dict()
    # header = 0, content = 1, footer = 2
    section = 0
    ebook['bookid'] = get_bookid(filepath)
    stems = []
    for line in StringIO(rawdata):
        # check to see if we advance to the next state
        if line.startswith('*** START'):
            section = 1
        elif line.startswith('*** END'):
            # no need to parse anymore, as we 
            #   dont index the footer
            break
        # otherwise process some text
        if section == 0:
            for key, value in key_map.items():
                if line.startswith('Release Date: '):
                    month, day, year = extract_date(extract_value('Release Date: ', line))
                    ebook['month'] = month
                    if day:
                        ebook['day'] = day
                    ebook['year'] = year
                elif line.startswith(key):
                    ebook[value] = extract_value(key, line)
        else:
            # perform preprocessing on the line so we can stem
            line = line.lower()
            line.replace('-', ' ')
            line = ''.join([c for c in line if c in alphabet])
            # stem the words in the line
            for word in line.split(' '):
                stem = stemmer.stem(word)
                if stem != '':
                    stems.append(stem)
    ebook['filepath'] = filepath
    ebook['stemmings'] = stems
    return ebook

def write_ebooks(books, stemmings):
    print('Books =', books)
    pass

def main():
    data_dir = os.path.join('data', 'aleph.gutenberg.org')
    try:
        books = []
        stemmings = []
        for r, dirs, _ in os.walk(data_dir):
            for d in dirs:
                # get just the text files
                for filename in [os.path.join(r, d, f) for f in os.listdir(os.path.join(r, d)) if f.endswith('.txt')]:
                    ebook = get_ebook(filename)
                    if ebook:
                        books.append({key:value for key, value in ebook.items() if key != 'stemmings'})
                        stemmings.append({'bookid':ebook['bookid'], 'stemmings':ebook['stemmings']})
                    # write books in batches of 10
                    if len(books) == 10:
                        write_ebooks(books, stemmings)
                        books.clear()
                        stemmings.clear()
    except IOError:
        print('Error: There was an error reading the data directory, cannot continue!')
        sys.exit(5)

if __name__ == '__main__':
    main()
