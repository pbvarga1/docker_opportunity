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
            console.log($ctrl.cameras)
            $ctrl.imageName = '';
            $ctrl.url = '';
            $ctrl.productType = '';
            $ctrl.camera = '';
            $ctrl.detatched = null;
        }

        $ctrl.ok = function () {
            $ctrl.close({
                $value: {
                    imageName: $ctrl.imageName,
                    url: $ctrl.url,
                    productType: $ctrl.productType,
                    camera: $ctrl.camera,
                    detatched: $ctrl.detatched,
                }
            });
        };
    }
});