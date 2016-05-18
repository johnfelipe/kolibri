/*
 * This file defines the base webpack configuration that is shared across both build and testing environments.
 * If you need to add anything to the general webpack config, like adding loaders for different asset types, different
 * preLoaders or Plugins - they should be done here. If you are looking to add dev specific features, please do so in
 * webpack.config.dev.js - if you wish to add test specific features, these can be done in the karma.conf.js.
 *
 * Note:
 * this file is not called directly by webpack.
 * It is called once for each plugin by parse_bundle_plugin.js
 */

var webpack = require('webpack');
var utils = require('./utils')

var config = {
    module: {
        preLoaders: [
          {
              test: /\.vue$/,
              loader: 'eslint',
              exclude: /node_modules/
          },
          {
              test: /\.js$/,
              loader: 'eslint',
              exclude: /node_modules/
          }
        ],
        loaders: [
            {
              test: /\.vue$/,
              loader: 'vue'
            },
            {
                test: /\.js$/,
                loader: 'babel',
                exclude: /node_modules/
            },
            {
                test: /fg-loadcss\/src\/onloadCSS/,
                loader: 'exports?onloadCSS'
            },
        ]
    },
    plugins: [
    ],
    resolve: {
        // shortcut to allow importing the core kolibri_module from other bundles (plugins)
        alias: {
            'kolibri_module': 'kolibri/core/assets/src/kolibri_module'
        }
    },
    eslint: {
        failOnError: true
    },
    vue: {
        loaders: utils.cssLoaders()
    }

};

module.exports = config;
