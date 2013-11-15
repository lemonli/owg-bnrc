'usr strict';

angular.module('bridgeapp', []).
  config(['$routeProvider', function($routeProvider) {
      $routeProvider.
          when('/bridges', {templateUrl: 'partials/bridge-list.html',
              controller: BridgeListCtrl}).
          when('/bridges/:bridgeId', {templateUrl: 'partials/bridge-detail.html',
              controller: BridgeDetailCtrl}).
          otherwise({redirectTo: '/bridges'});
}]).filter('range', function() {
  return function(input, total) {
    total = parseInt(total);
    for (var i=0; i<total; i++) {
      input.push(i);
    }
    return input;
  };
}).filter('fields', function() {
    return function(input) {
        var result = "";
        for (var field in input) {
            result += field + "=" + input[field] + ",";
        }
        return result;
    };
});
