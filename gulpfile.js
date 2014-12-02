// Load plugins
var gulp					= require('gulp');
var sass					= require('gulp-sass');
var sync					= require('browser-sync');
var size					= require('gulp-size');
var rename				= require('gulp-rename');
var minify				= require('gulp-minify-css');
var please				= require('gulp-pleeease');
var file					= require('gulp-file-include');


gulp.task('build-html', function() {
	gulp.src(['src/index.html'])	
		.pipe(file({
			prefix: '@@',
			basepath: '@file'
		}))
		.pipe(gulp.dest('./'));
});


gulp.task('build-css', function() {
	gulp.src(['src/css/index.scss'])
		.pipe(sass({ includePaths: ['./src/css/'] }))
		.pipe(please({ minifier: false, next: true }))
		.pipe(minify())
		.pipe(rename('site.css'))
		.pipe(gulp.dest('./'))
		.pipe(sync.reload({ stream: true}));
});


gulp.task('reload', ['build-html'], function() {
	sync.reload();
});

gulp.task('sync', ['build-css', 'build-html'], function() {
	sync({
		server: { baseDir: './' }
	});
});

gulp.task('watch', function() {
	gulp.watch('src/css/*.scss', ['build-css']);
	gulp.watch(['index.html', 'src/**/*.html'], ['rebuild-html']);
});


gulp.task('default', ['build-html', 'build-css', 'sync', 'reload'], function() {
	gulp.watch('src/**/*.scss', ['build-css']);
	gulp.watch(['*.html', 'src/**/*.html'],  ['reload']);
	gulp.watch('*.css', ['reload']);
});
