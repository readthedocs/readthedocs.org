var gulp = require('gulp'),
    browserify = require('gulp-browserify'),
    gulp_util = require('gulp-util'),
    run = require('gulp-run'),
    debowerify = require('debowerify');

/* Doc embed scripts */
gulp.task('browserify', function () {
    gulp.src(['readthedocs/core/static-src/core/js/readthedocs-doc-embed.js'])
        .pipe(browserify({
            transform: ['debowerify']
        }))
        .on('error', function (event) {
            gulp_util.log(event.message);
        })
        .pipe(gulp.dest('readthedocs/core/static/core/js/'));
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
