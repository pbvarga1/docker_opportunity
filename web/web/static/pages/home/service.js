angular.module('homeApp').service('homeService', function($http) {
    this.createProductType = function(name) { 
        return $http.post('/product_types', data={name: name});
    }
    this.getProductTypes = function() { 
        return $http.get('/product_types');
    }
    this.createCamera = function(name) { 
        return $http.post('/cameras', data={name: name});
    }
    this.getCameraNames = function() { 
        return $http.get('/cameras');
    }
    this.getImages = function() {
        return $http.get('/images');
    }
    this.registerImage = function(data) {
        return $http.post('/images', data=data);
    }
});