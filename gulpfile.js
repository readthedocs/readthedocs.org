var gulp = require('gulp'),
    browserify = require('gulp-browserify'),
    gulp_util = require('gulp-util'),
    run = require('gulp-run'),
    debowerify = require('debowerify');

/* Applications with static sources */
var sources = {
    'readthedocs/core': [
        'readthedocs/core/static-src/**/readthedocs-doc-embed.js'
    ],
    'readthedocs/projects': [
        'readthedocs/projects/static-src/**/tools.js'
    ],
    'readthedocs/gold': [
        'readthedocs/gold/static-src/**/gold.js'
    ],
    'readthedocs/donate': [
        'readthedocs/donate/static-src/**/donate.js'
    ]
};

/* Doc embed scripts */
gulp.task('browserify', function () {
    for (application in sources) {
        gulp.src(sources[application])
            .pipe(browserify({
                transform: ['debowerify']
            }))
            .on('error', function (event) {
                gulp_util.log(event.message);
            })
            .pipe(gulp.dest(application + '/static/'));
    }
});

gulp.task('collect', function () {
    gulp_util.log('Collecting static files');
    run('readthedocs/manage.py collectstatic --noinput')
        .exec();
});

/* Tasks */
gulp.task('build', ['browserify', 'collect']);

gulp.task('dev', ['build', 'watch']);

gulp.task('watch', function () {
    gulp.watch('readthedocs/**/static-src/**/*.js', ['build']);
});

gulp.task('default', ['build']);
