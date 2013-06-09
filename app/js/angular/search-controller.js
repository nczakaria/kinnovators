'use strict';

/* Controller for search.html */

//angular.module('app', ['ngResource']);
function SearchController($scope,$resource,sharedProperties){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
  
  $scope.backend_locations = [
    {url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.showdetails = false;
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };
  
  $scope.search = "";
  $scope.predicate_users = '-created';
  
  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.janrain_ref = sharedProperties.getJanrainAccount();
  $scope.waiting = "Ready";
  $scope.test = "-";
  $scope.notify = "You have no new notification(s).";
  
  //resource calls are defined here

  $scope.Model = $resource('http://:remote_url/:model_type/:id',
                          {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                             }
                      );
                          
  $scope.getuser = function(){
    $scope.UserResource = $resource('http://:remote_url/user/getuser',
                        {'remote_url':$scope.remote_url},
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  
    $scope.waiting = "Updating";       
    $scope.UserResource.get(function(response) {
          var result = response;
          $scope.iiii = result.u_login;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.get_notification();            
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
          }
          $scope.waiting = "Ready";
    });
  }

  $scope.setTest = function(test) {
    $scope.search = test;
  }
   $scope.get_notification = function() {
    $scope.NotificationResource = $resource('http://:remote_url/get/notification/:limit',
    {"remote_url":$scope.remote_url,"limit":3}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.NotificationResource.get(function(response) { 
        $scope.smallnotifications = response;
        if ($scope.smallnotifications.entities.length > 0) {
          $scope.notify = "You have " + $scope.smallnotifications.entities.length + " new notification(s).";
        }
        $scope.waiting = "Ready";
     });  
  };


  
  $scope.accept = {};
  $scope.accept.data = {'u_g' : 0, 'n_id': 0, 'status': 'accept'};
  $scope.notify_accept_group = function(n_a) {
    $scope.accept.data = n_a;
    $scope.AcceptResource = $resource('http://:remote_url/acceptreject/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Updating";
    var acceptgroup = new $scope.AcceptResource($scope.accept.data);
    acceptgroup.$save(function(response) { 
            var result = response;
            $scope.accept.data = {'u_g' : 0, 'n_id': 0, 'status': 'accept'};            
            $scope.get_notification();
          }); 
  };
  $scope.searchlist = function(){
    $scope.SearchResource = $resource('http://:remote_url/list/sketch/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.search}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";   
    $scope.SearchResource.get(function(response) { 
        $scope.searchitems = response;
        $scope.waiting = "Ready";
    });
  };
  
  $scope.getuser();
}