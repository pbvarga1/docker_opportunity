angular.module('createApp').component('create', {
    templateUrl: '/static/pages/create_entries/template.html',
    bindings: {
        title: '@',
        endpoint: '@',
        label: '@',
    },
    controller: function(createService) {
        $ctrl = this;

        $ctrl.$onInit = function() {
            $ctrl.newName = '';
            $ctrl.items = null;
            $ctrl.serviceEndpoint = $ctrl.endpoint;
            console.log($ctrl.title);
            console.log($ctrl.endpoint);
            setItems();
            console.log($ctrl.items)
        }

        function setItems() {
            createService.getItems($ctrl.serviceEndpoint).then(
                function(data) {
                    $ctrl.items = data.data.data;
                },
                function(data) {
                    console.log('EROR');
                    console.log(data);
                })
            ;
        }

        $ctrl.createItem = function() {
            createService.createItem($ctrl.serviceEndpoint, $ctrl.newName).then(
                function(data) {
                    $ctrl.newName = '';
                    setItems();
                },
                function(data) {
                    console.log('EROR');
                    console.log(data);
                }
            );
        }
    },
});