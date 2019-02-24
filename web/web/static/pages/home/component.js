angular.module('homeApp').component('home', {
    templateUrl: '/static/pages/home/template.html',
    controller: function homeController($timeout, homeService) {
        $ctrl = this;
        $ctrl.productTypeName = '';
        $ctrl.selectedProductTypeName = '';
        $ctrl.productTypes = [];
        setProductTypes();

        function setProductTypes() {
            homeService.getProductTypes().then(function(data) {
                console.log(data.data.names);
                $ctrl.productTypes = data.data.names;
                console.log($ctrl.productTypes);
            });
        }

        $ctrl.createProductType = function() {
            homeService.createProductType($ctrl.productTypeName).then(function(data) {
                setProductTypes();
            })
        }
    }
});