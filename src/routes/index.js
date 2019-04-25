var express = require('express');
// note: snowball is used for consistency, since I also
// used it to generate the stemmed words for the index
var snowball = require('snowball');
var router = express.Router();

// load in the English stemmer
const stemmer = new snowball('English');

/* 
 * Defines the page ranking function.
 * Takes in a collection of sorted stems and outputs the top 100 search results as 
 * a collection of JSON documents.
 */
function rank(stems) {
    return new Promise(function (resolve, reject) {
        var m_client = require('mongodb').MongoClient;
        var m_url = "mongodb://127.0.0.1:27017/";
        m_client.connect(m_url, function(err, db) {
            if (err) return [];
            var dbo = db.db("pgdb");
            db.collection("books").aggregate([
                // this stage gets the document frequency
                {$lookup: {
                        from: "doc_freqs",
                        localField: "bookid",
                        foreignField: "bookid",
                        as: "joined_terms"
                    }
                },
                // this stage converts the document frequency to a format we can work with
                {$project: {"book_terms": {$arrayElemAt: ["$joined_terms.terms", 0]}}},
                {$project: {"book_terms": {$objectToArray: "$book_terms"}}},
                // this stage gets the collection frequency, this is the bottleneck stage
                // there has to be a way to optimize it
                {$lookup: {
                        from: "coll_freqs",
                        localField: "book_terms.k",
                        foreignField: "_id",
                        as: "tfd_index"
                    }
                },
                // this stage replaces each document with an array of terms, an array of document freqs, and an array of collection freqs
                {$replaceRoot: { newRoot: { terms: "$book_terms.k", dfs: "$book_terms.v", cfs: "$tfd_index.value" } } }
            ]).toArray(function(err, res) {
                if (err) return reject(err);
                db.close();
                resolve(res); // return the result set as JSON
            });
        });
    });
}

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'PGDB Search Engine' });
});

/* GET search page */
router.get('/search', function(req, res, next) {
  try {
    // get the query and stem it
    var stemmed = [];
    var terms = req.query.querystr.toLowerCase().split(" ");
    for (var i = 0; i < terms.length; i++) {
        stemmer.setCurrent(terms[i]);
        stemmer.stem();
        stemmed.push(stemmer.getCurrent());
    }
    // sort the stems
    stemmed.sort();
    var promise = rank(stemmed);
    promise.then(function handleSearchResults(top100) {
        console.log(top100);
        res.render('search', { 
          title: 'Search Results',
          docs: top100
        });
    }).catch(function handleErrors(error) {
        res.render('error', {
          message: '500 Internal Server Error',
          error: {status: 'There was an error retrieving the search results, try again!', stack: error}
        }); 
    });
    
  } 
  catch (error) {
    res.render('error', {
      message: '500 Internal Server Error',
      error: {status: 'There was an error retrieving the search results, try again!', stack: error}
    }); 
  } 
});

module.exports = router;
