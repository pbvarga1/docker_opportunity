var app = angular.module('app', ['homeApp', 'createApp']);
app.config(function($routeProvider, $locationProvider) {
    $routeProvider
    .when("/", {
        template: '<home></home>'
    })
    .when("/product_types",{
        template: '<create title="Product Types" endpoint="/services/product_types" label="Product Type"></create>'
    })
    .when("/cameras",{
        template: '<create title="Cameras" endpoint="/services/cameras" label="Camera"></create>'
    });
    $locationProvider.html5Mode({
        enabled: true,
        requireBase: false
    });
});
