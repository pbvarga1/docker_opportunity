angular.module('homeApp').component('home', {
    templateUrl: '/static/pages/home/template.html',
    controller: function homeController($timeout, homeService) {
        $ctrl = this;
        $ctrl.productTypeName = '';
        $ctrl.selectedProductTypeName = '';
        $ctrl.productTypes = [];
        $ctrl.cameraName = '';
        $ctrl.selectedcameraName = '';
        $ctrl.cameraNames = [];
        setProductTypes();
        setCameraNames();

        function setProductTypes() {
            homeService.getProductTypes().then(function(data) {
                $ctrl.productTypes = data.data.names;
            });
        }

        $ctrl.createProductType = function() {
            homeService.createProductType($ctrl.productTypeName).then(function(data) {
                setProductTypes();
            })
        }

        function setCameraNames() {
            homeService.getCameraNames().then(function(data) {
                $ctrl.cameraNames = data.data.names;
            });
        }

        $ctrl.createCamera = function() {
            homeService.createCamera($ctrl.cameraName).then(function(data) {
                setCameraNames();
            })
        }
    }
});