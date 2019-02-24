angular.module('homeApp').service('homeService', function($http) {
    this.createProductType = function(name) { 
        return $http.post('/product_types', data={name: name});
    }
    this.getProductTypes = function() { 
        return $http.get('/product_types');
    }
});