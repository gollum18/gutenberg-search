const mongoose = require('mongoose');

var eBookSchema = new mongoose.Schema({
    _id: mongoose.Schema.Types.ObjectId,
    bookid: String,
    filepath: String,
    title: String,
    author: String,
    posting_date: String,
    release_date: String,
    langauge: String,
    char_set: String
});

module.exports = mongoose.model('ebook', eBookSchema);
