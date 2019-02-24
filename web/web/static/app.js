var app = angular.module('app', ['ngRoute', 'homeApp']);
app.config(function($routeProvider) {
    $routeProvider
    .when("/", {
        template: '<home></home>'
    });
});
