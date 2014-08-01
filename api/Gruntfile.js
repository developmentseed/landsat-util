// USGS Landsat Imagery Metadata RES API Gruntfile
//
// Forked from https://github.com/FDA/openfda/tree/master/api
// Exposes /landsat/metadata.json and /healthcheck GET endpoints
//
// Author: developmentseed
// Contributer: scisco
//
// License: CC0 V1

module.exports = function(grunt) {
  var path = require('path');

  grunt.loadNpmTasks('grunt-contrib-nodeunit');

  grunt.initConfig({
    nodeunit: {
      all: ['*_test.js'],
      options: {
        reporter: 'verbose'
      }
    }
  });
};
