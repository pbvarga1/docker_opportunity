angular.module('homeApp').component('home', {
    templateUrl: '/static/pages/home/template.html',
    controller: function homeController($uibModal, $timeout, homeService) {
        $ctrl = this;
        $ctrl.productTypeName = '';
        $ctrl.selectedProductType = null;
        $ctrl.productTypes = [];
        $ctrl.camera = '';
        $ctrl.selectedCamera = null;
        $ctrl.cameras = [];
        $ctrl.allImages = [];
        $ctrl.progress = {};
        $ctrl.imageSrc = '';
        setProductTypes();
        setCameras();
        setImages().then(function (data){
            cacheImages(data);
            setImages();
        });

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
            return homeService.getImages().then(function(data) {
                $ctrl.allImages = data.data.data;
                return data.data.data;
            });
        }

        function cacheImage(image) {
            return homeService.cacheImage(image);
        }

        function cacheImages(images) {
            return angular.forEach(images, function(image, idx) {
                cacheImage(
                    {
                        url: image['URL'],
                        name: image['Name']
                    }
                );
                setProgress(image['Name'])
            });
        }

        $ctrl.setProgress = function(ID) {
            var progress = -1;
            progressPromise = homeService.getProgress(ID).then(
                function(data) {
                    progress = data.data.data;
                    if (progress == -1) {
                        $timeout(function() {
                            $ctrl.setProgress(ID)
                        }, 300);
                    } else {
                        progress = progress * 100;
                        $ctrl.progress[ID] = progress
                        $timeout(function() {
                            $ctrl.setProgress(ID)
                        }, 100);
                    }
                    return progress
                },
                function(data) {
                    console.log('ERROR');
                    return 100;
                }
            );
            return progressPromise;
            
        };

        $ctrl.getProgress = function(ID) {
            var progress = $ctrl.progress[ID];
            if (progress === null)
                return 100;
            else
                return progress;
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
                    var image;
                    homeService.registerImage(new_image).then(function(data) {
                        image = data.data.data;
                        setImages().then(function(data) {
                            cacheImage(
                                {
                                    url: image['URL'],
                                    name: image['Name']
                                }
                            ).then(function() {
                                setImages();
                            });
                            $ctrl.setProgress(image['Name']);
                        });
                    });
                },
                function() {
                    null;
                }
            );
        };

        $ctrl.getImageSource = function(image) {
            return '/services/display_image?url=' + image['URL'];
        }

        $ctrl.onImageError = function() {
            console.log('ERROR');
            $ctrl.imageSrc = '';
        }
    }
});