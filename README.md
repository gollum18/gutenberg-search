# guttenberg-search
Guttenberg Project search engine built using a multi-phase inverted index, tf.idf, and vector ranking to retrieve relevant books to their search query. This should be wrapped in a nice web front-end (probably in Node.js with Express/Pug), that functions similarly to Google or Bing, although since I despise CSS, it won't look as pretty.

## inverted index?
An inverted index is just a really big flat file (well two technically), that is constructed in several steps (this is a general way to do it, not the specific steps):

Given a collection of N documents perform the following for each document in the collection:
1. Assign a document ID to the document.
2. Initialize some structure to map terms and document ids to frequencies
3. For each document in the collection:  
  1. Initialize some structure to map terms to frequency.
  2. For each word in the document:  
    1. If the word is a stop word, then skip it (optional, but improves the speed/size of the index)  
    2. Otherwise, stem the word (since words like friends/friendly become friend, should be considered the same)  
    3. If the word is not in the structure made earlier, add it and initialize it's frequency to 1  
    4. Otherwise, increment the words frequency in the structure by 1.  
  3. For each word/frequency pair in the tf structure:  
    1. Extract the word and frequency  
    2. Write the word and document as the key and the frequency as the value in the structure made in step 2 way above.  
  4. Write the term frequency structure to a datastore
4. Sort the structure made in step 2, first lexicographically by the term, and then numerically by the document id.
5. Write this structure to a datastore
6. Flatten the structure by creating yet another structure to hold just the document id and frequency.
7. Write this structure to datastore.
8. The structures you created in steps 5 and 7 are known respectively as a dictionary 'file' and a postings 'file' and they, together, constitute the inverted index.

## tf.idf?
tf.idf or (T)erm (F)requency * (I)nverted (D)ocument (F)requency is a fundamental information retrieval technique. It attempts to balance the issues that arise from relating queries to documents by utilizng the term frequency via weighting with document frequency. Inverted document frequency is used to ensure that the rarest search terms that appear in a query over a collection of documents have higher weight then more common search terms (as documents containing rarer words are considered to be more relevant to the search query than documents containing less rare words. This is similar to the techniques employed for the very early version of the Google search engine (which since, has become vastly more complicated).

Rarity of a word is defined using: 
- The term frequency: the amount of times a term appears in a single document
- The document frequency: the amount of documents a term appears in at least once (cannot be greater than N, the size of the document collection)
- The collection frequency: the total amount of times the term appears across all documents in the collection

## vector ranking?
Vector ranking is a query/document scoring mechanism that utilizes a so-called [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) index to compute the angle of intersection between the query plane and the document plane. The closer the angle is to zero, the more relevant the document is to the query and the higher its overall ranking in the returned results to the user. A fully orthoganal cosine similiarity index indicates that the document is not relevant at all to the query and should not be returned in the result set. It's nice, I'm actually using something I learned in Calculus for a real world application.

## can I contribute?
Not yet! Any contributions will have to wait until this status is updated. This is a term project for CIS 612: Big Data and Parallel Database Systems and I am required to build it by myself. I would gladly accept any assistance once I submit it though.
