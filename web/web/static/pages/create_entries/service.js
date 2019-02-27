angular.module('createApp').service('createService', function($http) {
    this.createItem = function(endpoint, name) { 
        return $http.post(endpoint, data={name: name});
    }
    this.getItems = function(endpoint) { 
        return $http.get(endpoint);
    }
});