var bodyParser = require('body-parser');
var express = require('express');
// note: snowball is used for consistency, since I also
// used it to generate the stemmed words for the index
var snowball = require('snowball');
var router = express.Router();

// load in the model
var ebook = require('../models/ebook.js');

// load in mongoose
const mongoose = require('mongoose');

// load in the English stemmer
const stemmer = new snowball('English');

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'PGDB Search Engine' });
});

/* POST search page */
router.get('/search', function(req, res, next) {
  var query_promise = new Promise(function(resolve, reject) {
    // get the query and stem it
    var query = req.body.txt_input;
    var stemmed = [];
    for (var word in query.split(" ")) {
      stemmer.setCurrent(word);
      stemmer.stem();
      stemmed.push(stemmer.getCurrent());
    }
    // connect to MongoDB
    // pass the stemmed words off to MongoDB M/R
    mongoose.connect('mongodb://localhost:27017/pgdb', {useNewUrlParser: true});
    var db = mongoose.connection();
    db.on('error', console.error.bind(console, 'connection error:'))
    db.once('open', function() {
      
    });
    return stemmed;
  }).then(function(result) {
    res.render('search', { 
      title: 'Search Results',
      docs: result 
    });
  }, function(error) {
    res.render('error', { title: error });  
  });
});

module.exports = router;
