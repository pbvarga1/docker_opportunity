angular.module('homeApp').component('home', {
    templateUrl: '/static/pages/home/template.html',
    controller: function homeController($uibModal, homeService) {
        $ctrl = this;
        $ctrl.productTypeName = '';
        $ctrl.selectedProductType = null;
        $ctrl.productTypes = [];
        $ctrl.camera = '';
        $ctrl.selectedCamera = null;
        $ctrl.cameras = [];
        $ctrl.allImages = [];
        $ctrl.imageSrc = '';
        setProductTypes();
        setCameras();
        setImages();

        function setProductTypes() {
            homeService.getProductTypes().then(function(data) {
                $ctrl.productTypes = data.data.data;
            });
        }

        $ctrl.createProductType = function() {
            homeService.createProductType($ctrl.productTypeName).then(function(data) {
                setProductTypes();
            })
        }

        function setCameras() {
            homeService.getCameraNames().then(function(data) {
                $ctrl.cameras = data.data.data;
            });
        }

        $ctrl.createCamera = function() {
            homeService.createCamera($ctrl.cameraName).then(function(data) {
                setCameras();
            })
        }

        function setImages() {
            homeService.getImages().then(function(data) {
                $ctrl.allImages = data.data.data;
            });
        }

        $ctrl.openCreateImage = function() {
            var modalInstance = $uibModal.open({
                component: 'createImageComponent',
                resolve: {
                    cameras: function() {
                        return $ctrl.cameras;
                    },
                    productTypes: function() {
                        return $ctrl.productTypes;
                    }
                }
            });

            modalInstance.result.then(
                function(new_image) {
                    homeService.registerImage(new_image).then(function(data) {
                        setImages();
                    });
                },
                function() {
                    null;
                }
            );
        };

        $ctrl.displayImage = function() {
            console.log('/display_image?url=' + $ctrl.selectedImage['URL']);
            $ctrl.imageSrc = '/display_image?url=' + $ctrl.selectedImage['URL'];
        };

        $ctrl.onImageError = function() {
            console.log('ERROR');
            $ctrl.imageSrc = '';
        }
    }
});