var gulp = require('gulp'),
    gulp_util = require('gulp-util'),
    watch = require('gulp-watch'),
    run = require('gulp-run'),
    less = require('gulp-less'),
    bower_resolve = require('bower-resolve'),
    browserify = require('browserify'),
    debowerify = require('debowerify'),
    uglify = require('gulp-uglify'),
    vinyl_source = require('vinyl-source-stream'),
    vinyl_buffer = require('vinyl-buffer'),
    es = require('event-stream'),
    path = require('path'),
    pkg_config = require('./package.json');

// Applications with primary static sources. We define these here to avoid
// picking up dependencies of the primary entry points and putting any
// limitations on directory structure for entry points.
var sources = {
    core: [
        'js/readthedocs-doc-embed.js',
        'js/autocomplete.js',
        'js/projectimport.js',
    ],
    projects: ['js/tools.js'],
    gold: ['js/gold.js'],
    donate: ['js/donate.js']
};

// Standalone application to create vendor bundles for. These can be imported
// with require in the browser or with Node during testing.
var standalone = ['jquery', 'knockout'];

// Build application call, wraps building entry point files for a single
// application. This is called by build and dev tasks.
function build_app_sources (application, minify) {
    // Normalize file glob lists
    var app_sources = sources[application].map(function (n) {
        return path.join(pkg_config.name, application, 'static-src', '**', n)
    });
    var app_js_sources = app_sources.filter(function (elem, n, arr) {
        return /\.js$/.test(elem);
    });
    var app_css_sources = app_sources.filter(function (elem, n, arr) {
        return /\.less$/.test(elem);
    });

    // Javascript sources
    var app_js = gulp
        .src(app_js_sources)
        .pipe(es.map(browserify_stream));

    if (minify) {
        app_js = app_js
            .pipe(vinyl_buffer())
            .pipe(uglify())
            .on('error', function (ev) {
                gulp_util.beep();
                gulp_util.log('Uglify error:', ev.message);
            });
    }

    // CSS sources
    var app_css = gulp.src(app_css_sources)
        .pipe(less({}))
        .on('error', function (ev) {
            gulp_util.beep();
            gulp_util.log('LESS error:', ev.message);
        });

    return es.merge(app_js, app_css)
        .pipe(gulp.dest(path.join(pkg_config.name, application, 'static')));
}

// Browserify build
function browserify_stream (file, cb_output) {
    bower_resolve.offline = true;
    bower_resolve.init(function () {
        var bundle_stream = browserify(file.path)

        standalone.map(function (module) {
            bundle_stream = bundle_stream.external(module);
        });

        bundle_stream
            .transform('debowerify', {ignoreModules: standalone})
            .bundle()
            .on('error', function (ev) {
                gulp_util.beep();
                gulp_util.log('Browserify error:', ev.message);
            })
            .pipe(vinyl_source(file.path, file))
            .pipe(es.map(function (data, cb_inner) {
                cb_output(null, data);
            }));
    });
}

// Build standalone vendor modules
function build_vendor_sources(data, cb_output) {
    bower_resolve.offline = true;
    bower_resolve.init(function () {
        var standalone_modules = standalone.map(function (module) {
            return browserify({standalone: module})
                .require(bower_resolve(module), {expose: module})
                .bundle()
                .pipe(vinyl_source(module + '.js'))
                .pipe(vinyl_buffer())
                .pipe(uglify())
                .pipe(gulp.dest(path.join(pkg_config.name, 'static', 'vendor')));
        });

        es
            .merge(standalone_modules)
            .pipe(es.wait(function (err, body) {
                cb_output(null, data);
            }));
    });
}

/* Tasks */
gulp.task('build', function (done) {
    gulp_util.log('Building source files');

    es
        .merge(Object.keys(sources).map(function (n) {
            return build_app_sources(n, true);
        }))
        .pipe(es.wait(function (err, body) {
            gulp_util.log('Collecting static files');
            run('./manage.py collectstatic --noinput')
                .exec('', function (err) { done(err); });
        }));
});

gulp.task('vendor', function (done) {
    build_vendor_sources(null, done);
});

gulp.task('dev', function (done) {
    gulp_util.log('Continually building source files');

    es
        .merge(Object.keys(sources).map(function (application) {
            var files = [
                path.join(pkg_config.name, application, 'static-src', '**', '*.js'),
                path.join(pkg_config.name, application, 'static-src', '**', '*.css')
            ];
            return watch(files, {verbose: true, name: 'dev'}, function () {
                build_app_sources(application, false)
                    .pipe(es.wait(function (err, body) {
                        gulp_util.log('Collecting static files');
                        run('./manage.py collectstatic --noinput').exec('');
                    }));
            });
        }))
        .pipe(es.wait(function (err, body) {
            done(null);
        }));
});

gulp.task('default', ['build']);
