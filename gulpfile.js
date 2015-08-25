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
    builds: {'js/detail.js': {}},
    core: {
        'js/readthedocs-doc-embed.js': {create_module: false},
        'js/autocomplete.js': {},
        'js/projectimport.js': {},
    },
    projects: {'js/tools.js': {}},
    gold: {'js/gold.js': {}},
    donate: {'js/donate.js': {}}
};

// Standalone application to create vendor bundles for. These can be imported
// with require in the browser or with Node during testing.
var standalone = {
    'jquery': {standalone: 'jquery'},
    'knockout': {},
    'jquery-migrate': {standalone: 'jquery-migrate'},
    'jquery-ui': {standalone: 'jquery-ui'},
    'underscore': {standalone: '_'}
};

// Build application call, wraps building entry point files for a single
// application. This is called by build and dev tasks.
function build_app_sources (application, minify) {
    // Normalize file glob lists
    var bundles = Object.keys(sources[application]).map(function (n) {
        var bundle_path = path.join(
                pkg_config.name, application, 'static-src', '**', n),
            bundle_config = sources[application][n] || {},
            bundle;

        if (/\.js$/.test(bundle_path)) {
            // Javascript sources
            bundle = gulp
                .src(bundle_path)
                .pipe(es.map(function (file, cb) {
                    return browserify_stream(file, bundle_config, cb);
                }));

            if (minify) {
                bundle = bundle
                    .pipe(vinyl_buffer())
                    .pipe(uglify())
                    .on('error', function (ev) {
                        gulp_util.beep();
                        gulp_util.log('Uglify error:', ev.message);
                    });
            }
        }
        else if (/\.less$/.test(bundle_path)) {
            // CSS sources
            bundle = gulp.src(bundle_path)
                .pipe(less({}))
                .on('error', function (ev) {
                    gulp_util.beep();
                    gulp_util.log('LESS error:', ev.message);
                });
        }

        return bundle;
    });

    return es.merge(bundles)
        .pipe(gulp.dest(path.join(pkg_config.name, application, 'static')));
}

// Browserify build
function browserify_stream (file, config, cb_output) {
    bower_resolve.offline = true;
    bower_resolve.init(function () {
        var bundle_stream = browserify();

        Object.keys(standalone).map(function (module) {
            bundle_stream = bundle_stream.external(module);
        });

        if (config.create_module === false) {
            bundle_stream.add(file.path)
        }
        else {
            var module_name = config.expose || path.basename(file.path, '.js');
            bundle_stream = bundle_stream.require(
                file.path,
                {expose: module_name})
        }

        bundle_stream
            .transform('debowerify', {ignoreModules: Object.keys(standalone)})
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
        var standalone_modules = Object.keys(standalone).map(function (module) {
            var vendor_options = standalone[module] || {},
                vendor_bundles = [];

            // Bundle vendor libs for import via require()
            vendor_bundles.push(
                browserify()
                .require(bower_resolve(module), {expose: module})
                .bundle()
                .pipe(vinyl_source(module + '.js'))
                .pipe(vinyl_buffer())
                .pipe(uglify())
                .pipe(gulp.dest(
                    path.join(pkg_config.name, 'static', 'vendor')
                ))
            );

            // Bundle standalone for legacy use. These should only be used on
            // old documentation that does not yet use the new bundles
            if (typeof(vendor_options.standalone) != 'undefined') {
                vendor_bundles.push(
                    browserify({standalone: vendor_options.standalone})
                    .require(bower_resolve(module))
                    .bundle()
                    .pipe(vinyl_source(module + '-standalone.js'))
                    .pipe(vinyl_buffer())
                    .pipe(uglify())
                    .pipe(gulp.dest(
                        path.join(pkg_config.name, 'static', 'vendor')
                    ))
                );
            }

            return es.merge(vendor_bundles);
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
                path.join(pkg_config.name, application, 'static-src', '**', '*.less')
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
