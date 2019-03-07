angular.module('homeApp').service('homeService', function($http) {
    this.getProductTypes = function() { 
        return $http.get('/services/product_types');
    }
    this.getCameraNames = function() { 
        return $http.get('/services/cameras');
    }
    this.getImages = function() {
        return $http.get('/services/images');
    }
    this.registerImage = function(data) {
        return $http.post('/services/images', data=data);
    }
    this.cacheImage = function(data) {
        return $http.post('/services/cache_image', data=data);
    }
    this.getProgress = function(ID) {
        return $http.post('/services/progress', data={ID: ID});
    }
});