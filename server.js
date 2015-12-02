/*
 * Copyright (C) 2015 Hauke Petersen <devel@haukepetersen.de>
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @fileoverview    Code size visualization server
 *
 * @author          Hauke Petersen <devel@haukepetersen.de>
 */

/**
 * Setup the base configuration
 */
const WEB_PORT = 12345;
const ROOT_DIR = __dirname + '/root/';

/**
 * include packages
 */
var express = require('express');
var app = express();
var server = require('http').createServer(app);

var is_alarm = false;

/**
 * Setup static routes for img, js, css and the favicon
 */
app.use('/img', express.static(ROOT_DIR));
app.use('/js', express.static(ROOT_DIR));
app.use('/css', express.static(ROOT_DIR));

/**
 * Setup Dynamic endpoints, depending on the internal state
 */
app.get('/*.csv', function(req, res) {
    console.log("delivering", req.url);
    res.sendFile(ROOT_DIR + req.url);
});

app.get('/*', function(req, res) {
    res.sendFile(ROOT_DIR + 'index.html');
});


/**
 * Bootstrap and start the application
 */
server.listen(WEB_PORT, function() {
    console.info('WEBSERVER: Running at http://127.0.0.1:' + WEB_PORT + '/');
});
