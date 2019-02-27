angular.module('homeApp').component('createImageComponent', {
    templateUrl: '/static/pages/home/modals/create_image.html',
    bindings : {
        resolve: '<',
        close: '&',
        dismiss: '&'
    },
    controller: function() {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            $ctrl.productTypes = $ctrl.resolve.productTypes;
            $ctrl.cameras = $ctrl.resolve.cameras;
            $ctrl.sol = null;
            $ctrl.url = '';
            $ctrl.productType = '';
            $ctrl.camera = '';
            $ctrl.detatched = false;
        }

        $ctrl.ok = function(){
            $ctrl.close({
                $value: {
                    sol: $ctrl.sol,
                    url: $ctrl.url,
                    productType: $ctrl.productType.ID,
                    camera: $ctrl.camera.ID,
                    detatched: $ctrl.detatched,
                }
            });
        };

        $ctrl.cancel = function(){
            $ctrl.dismiss({$value: 'cancel'});
        };
    }
});