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
            dbo.collection("books").aggregate([ 
                // this stage gets the document frequency
                { $lookup: 
                    {
                        from: "doc_freqs",
                        localField: "bookid",
                        foreignField: "bookid",
                        as: "joined_terms"
                    }
                },
                // this stage converts the document frequency to a format we can work with
                { $project: 
                    { 
                        title: "$title", 
                        filepath: "$filepath",
                        book_terms: { 
                            $filter: {
                                input: { $objectToArray: { $arrayElemAt: [ "$joined_terms.terms", 0 ] } },
                                as: "term_freq",
                                cond: { $in: [ "$$term_freq.k", stems ] }
                            }
                        }
                    } 
                },
                // I shouldnt have had to do this, but I'm relatively certain this is the only 
                //  way I can in MongoDB, have to reproject the stuff above with the same values
                //  plus a count of the book terms
                { $project: 
                    { 
                        title: "$title", 
                        filepath: "$filepath",
                        book_terms: "$book_terms",
                        count: { $size: "$book_terms" }
                    } 
                },
                // filter out the documents that do not have any matching book terms
                { $match: 
                    {
                        count: {$gt: 0}
                    } 
                },
                // this stage joins the collection frequency to the doc frequency
                { $lookup: 
                    {
                        from: "coll_freqs",
                        localField: "book_terms.k",
                        foreignField: "_id",
                        as: "tfd_index"
                    }
                },
                // this stage replaces each document with an array of terms, an array of document freqs, and an array of collection freqs
                { $replaceRoot: 
                    { newRoot: 
                        { 
                            title: "$title", 
                            filepath: "$filepath", 
                            terms: "$book_terms.k", dfs: "$book_terms.v", cfs: "$tfd_index.count" 
                        } 
                    } 
                },
                // zips all three arrays above into a single array containing arrays with three elements
                { $project: { 
                        title: "$title", 
                        filepath: "$filepath", 
                        index: { $zip: {inputs: ["$terms", "$dfs", "$cfs"] } } 
                    } 
                },
                // perform the tf.idf on the array above
                // TODO: The bookid needs passed along all the way here
                { $project: 
                    { title: "$title", 
                      filepath: "$filepath",
                      tfidf: 
                        { $map: 
                            {
                                input: "$index",
                                as: "tfidf",
                                in: { $multiply:
                                        [ 
                                            // this term is the tf
                                            { $log10: { 
                                                $add: [
                                                    1, 
                                                    { $arrayElemAt: [ "$$tfidf", 1 ] } 
                                                ] } 
                                            },
                                            // this term is the idf
                                            { $log10: { 
                                                $divide: [
                                                    // hard coded number of documents, best I can do for now
                                                    // TODO: it should really be passed all the way to this stage too, like bookid
                                                    9285, 
                                                    { $add: [ 1, { $arrayElemAt: [ "$$tfidf", 2 ] } ] } 
                                                ] } 
                                            }
                                        ] 
                                    }
                            }   
                        }
                    } 
                },
                // generate rankings for the pages
                { $project: 
                    {
                        title: "$title",
                        filepath: "$filepath",
                        ranking: { $reduce: {
                                input: "$tfidf",
                                initialValue: 0,
                                in: { $add: [ "$$value", "$$this" ] }
                            }
                        }
                    }
                },
                // sort the pages in descending order
                { $sort: { ranking: -1 } },
                // return the top 100 pages
                { $limit: 100 }
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
        // handle the search results
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
