'use strict'

function nullify(strut) {
    Object.keys(strut).forEach(function(key) {
        if (strut[key] != null && typeof strut[key] === 'object') {
            nullify(strut[key]);
        }
        else {
            strut[key] = null;
        }
    })
}

function BridgeListCtrl($scope, $http) {
    var promise = $http.get('/bridges');

    promise.then(function(response) {
            $scope.bridges = response.data.bridges;
    });

    $scope.add_br = function(brname) {
        $http({method: 'POST', url: '/bridges/add', params:{name:brname}}).
            success(function(data) {
                $scope.bridges = data.bridges;
            });
    }

    $scope.del_br = function(brname) {
        $http({method: 'POST', url: '/bridges/' + brname + '/del'}).
            success(function(data) {
                $scope.bridges = data.bridges;
            });
    }
}

function BridgeDetailCtrl($scope, $routeParams, $http, $location) {
    $scope.brname = $routeParams.bridgeId;

    var templates =
       [ { name: 'basic', url: '/partials/basic-info.html'}
       , { name: 'controller', url: '/partials/controller.html'}
       , { name: 'port', url:'/partials/ports.html'}
       , { name: 'tunnel', url:'/partials/tunnel.html'}
       , { name: 'lag', url:'/partials/lag.html'}
       , { name: 'mirror', url:'/partials/mirror.html'}
       , { name: 'netflow', url:'/partials/netflow.html'}
       , { name: 'sflow', url:'/partials/sflow.html'}
       , { name: 'Queue', url:'/partials/queue.html'}
       , { name: 'QoS', url:'/partials/qos.html'}
       , { name: 'Flow', url:'/partials/flow.html'}];

    $scope.template = templates[0];

    $scope.viewSection = function(index) {
        $scope.template = templates[index];
    }

    $scope.br = null;
    var promise = $http.get('/bridges/'+$scope.brname);

    promise.then(function(response) {
        $scope.br = response.data.bridge;
    });

    $scope.goback = function() {
        $location.path('/bridges');
    };
}

function BasicInfoCtrl($scope, $http) {
    $scope.modes = ['secure', 'standalone'];
    $scope.enable = [true, false];

    $scope.update_bridge = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/update', record);
        promise.then(function(response) {
            $scope.br = response.data.bridge;
        });
    };
}

function ControllerCtrl($scope, $http) {
    $scope.controllers = $scope.br.controller;
    $scope.new_ctrl = {"protocol":null, "ip":null, "port":null, "connection_mode":null};

    $scope.protocols = ['ptcp', 'tcp', 'ssl', 'pssl'];
    $scope.mode = ['in-band', 'out-of-band'];
    $scope.bool = [true, false];
    $scope.namedbool = [ { "label": "enable", "value": true },
        { "label": "disable", "value": "false"} ];
    $scope.role = ['slave', 'other', 'master'];

    $scope.update_ctrl= function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/controllers/update', record);
        promise.then(function(response) {
            $scope.controllers = response.data.controllers;
            $scope.br.controller = $scope.controllers;
        });
    };

    $scope.del_ctrl = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/controllers/del', record);
        promise.then(function(response) {
            $scope.controllers = response.data.controllers;
            $scope.br.controller = $scope.controllers;
        });
    };

    $scope.add_ctrl = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/controllers/add', record);
        promise.then(function(response) {
            $scope.controllers = response.data.controllers;
            $scope.br.controller = $scope.controllers;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        Object.keys($scope.new_ctrl).forEach(function(key) {
            $scope.new_ctrl[key] = null;
        });
    };

    //var promise = $http.get('/bridges/'+$scope.brname+'/controllers');
    //promise.then(function(response) {
        //$scope.controllers = response.data.controllers;
    //});
}

function PortsCtrl($scope, $http) {
    $scope.ports = $scope.br.ports;
    $scope.new_port = {
        "name":null,
        "vlan_config": {
            "vlan_mode":null,
            "tag":null,
            "trunks":null
        },
    }

    $scope.name = '+name';
    $scope.modes = ["access", "trunk"];
    $scope.update_port = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/ports/'+record.name+'/update', record);
        promise.then(function(response) {
            $scope.ports = response.data.ports;
            $scope.br.ports = $scope.ports;
        });
    };

    $scope.del_port = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/ports/'+record.name+'/del', record);
        promise.then(function(response) {
            $scope.ports = response.data.ports;
            $scope.br.ports = $scope.ports;
        });
    };

    $scope.add_port = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/ports/'+record.name+'/add', record);
        promise.then(function(response) {
            $scope.ports = response.data.ports;
            $scope.br.ports = $scope.ports;
        });
    };

    $scope.reset = function() {
        Object.keys($scope.new_port).forEach(function(key) {
            $scope.new_port[key] = null;
        });
    };
}

function TunnelCtrl($scope, $http) {
    $scope.tunnels = $scope.br.tunnels;
    $scope.new_tunnel = {
        "name":null,
        "remote_ip":null,
        "local_ip":null,
        "src_mac":null,
        "dst_mac":null,
        "egress_port":null,
        "vlan":null
    }

    $scope.name = '+name';
    $scope.update_tunnel = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/tunnels/'+record.name+'/update', record);
        promise.then(function(response) {
            $scope.tunnels = response.data.tunnels;
            $scope.br.tunnels = $scope.tunnels;
        });
    };

    $scope.del_tunnel = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/tunnels/'+record.name+'/del', record);
        promise.then(function(response) {
            $scope.tunnels = response.data.tunnels;
            $scope.br.tunnels = $scope.tunnels;
        });
    };

    $scope.add_tunnel = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/tunnels/'+record.name+'/add', record);
        promise.then(function(response) {
            $scope.tunnels = response.data.tunnels;
            $scope.br.tunnels = $scope.tunnels;
        });
    };

    $scope.reset = function() {
        Object.keys($scope.new_tunnel).forEach(function(key) {
            $scope.new_tunnel[key] = null;
        });
    };
}

function MirrorCtrl($scope, $http) {
    $scope.mirrors = $scope.br.Mirrors;
    $scope.name = '+name';
    $scope.new_mirror = {
        "name":null,
        "select_src_port":null,
        "select_dst_port":null,
        "output_port":null,
        "select_vlan":null,
        "output_vlan":null,
    };

    $scope.update_mirror = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/mirrors/'+record.name+'/update', record);
        promise.then(function(response) {
            $scope.mirrors = response.data.mirrors;
            $scope.br.Mirrors = $scope.mirrors;
        });
    };

    $scope.del_mirror = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/mirrors/'+record.name+'/del', record);
        promise.then(function(response) {
            $scope.mirrors = response.data.mirrors;
            $scope.br.Mirrors = $scope.mirrors;
        });
    };

    $scope.add_mirror = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/mirrors/'+record.name+'/add', record);
        promise.then(function(response) {
            $scope.mirrors = response.data.mirrors;
            $scope.br.Mirrors = $scope.mirrors;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        Object.keys($scope.new_mirror).forEach(function(key) {
            $scope.new_mirror[key] = null;
        });
    };
}

function QueueCtrl($scope, $http) {
    $scope.new_queue = {
        "dscp":null,
        "other_config":
            {
            "min-rate":null,
            "max-rate":null,
            "burst":null,
            "priority":null
            }
    }
    var promise = $http.get('/bridges/'+$scope.brname+'/queues');

    promise.then(function(response) {
        $scope.queues = response.data.queues;
    });

    $scope.update_queue = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/queues/'+record.uuid.slice(0,8)+'/update', record);
        promise.then(function(response) {
            $scope.queues = response.data.queues;
        });
    };

    $scope.del_queue = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/queues/'+record.uuid.slice(0,8)+'/del', record);
        promise.then(function(response) {
            $scope.queues = response.data.queues;
        });
    };

    $scope.add_queue = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/queues/add', record);
        promise.then(function(response) {
            $scope.queues = response.data.queues;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        nullify($scope.new_queue);
    };
}

function QoSCtrl($scope, $http) {
    $scope.new_qos = {
        "type":null,
        "queues":[],
        "other_config":{
            "max-rate":null,
            }
    };
    $scope.types = ['linux-htb', 'linux-hfsc'];

    $scope.new_cnt = 0;
    $scope.cnt = 0;

    var promise = $http.get('/bridges/'+$scope.brname+'/qos');

    promise.then(function(response) {
        $scope.qoses = response.data.qoses;
    });

    $scope.update_qos = function(record, cnt) {
        record.queues = record.queues.slice(0, cnt);
        var promise = $http.post('/bridges/'+$scope.brname+'/qos/'+record.uuid.slice(0,8)+'/update', record);
        promise.then(function(response) {
            $scope.qoses = response.data.qoses;
        });
    };

    $scope.del_qos = function(record) {
        var promise = $http.post('/bridges/'+$scope.brname+'/qos/'+record.uuid.slice(0,8)+'/del', record);
        promise.then(function(response) {
            $scope.qoses = response.data.qoses;
        });
    };

    $scope.add_qos = function(record, cnt) {
        record.queues = record.queues.slice(0, cnt);
        var promise = $http.post('/bridges/'+$scope.brname+'/qos/add', record);
        promise.then(function(response) {
            $scope.qoses = response.data.qoses;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        nullify($scope.new_qos);
        $scope.new_qos.queues = [];
        $scope.new_cnt = 0;
    };
}

function sFlowCtrl($scope, $http){
    $scope.sflow = $scope.br.sFlow;
    $scope.new_sflow = {
        "polling":null,
        "header":null,
        "targets":[],
        "agent":null,
        "sampling":null,
    };

    $scope.init_targets = function(cnt) {
       $scope.new_sflow.targets = [];
       for (var i = 0; i < cnt; i++) {
           $scope.new_sflow.targets.push({})
       }
    };

    $scope.update_sflow = function(record){
        var promise = $http.post('/bridges/'+$scope.brname+'/sflow/update', record);
        promise.then(function(response){
            $scope.sflow = response.data.sflow;
            $scope.br.sFlow = $scope.sflow;
        });
    };

    $scope.del_sflow = function(record){
        var promise = $http.post('/bridges/'+$scope.brname+'/sflow/del', record);
        promise.then(function(response){
            $scope.sflow = response.data.sflow;
            $scope.br.sFlow = $scope.sflow;
        });
    };

    $scope.add_sflow = function(record){
        record.targets = record.targets.slice(0, $scope.target_count);
        var promise = $http.post('/bridges/'+$scope.brname+'/sflow/add', record);
        promise.then(function(response){
            $scope.sflow = response.data.sflow;
            $scope.br.sFlow = $scope.sflow;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        nullify($scope.new_sflow);
        $scope.new_sflow.targets = [];
        $scope.target_count = null;
    };
}

function NetFlowCtrl($scope, $http){
    $scope.netflow = $scope.br.NetFlow;
    $scope.target_count = null;
    $scope.new_netflow = {
        "active_timeout":null,
        "targets":[],
    };

    $scope.init_targets = function(cnt) {
       $scope.new_netflow.targets = [];
       for (var i = 0; i < cnt; i++) {
           $scope.new_netflow.targets.push({})
       }
    };

    $scope.update_netflow = function(record){
        var promise = $http.post('/bridges/'+$scope.brname+'/netflow/update', record);
        promise.then(function(response){
            $scope.netflow = response.data.netflow;
            $scope.br.NetFlow = $scope.netflow;
        });
    };

    $scope.del_netflow = function(record){
        var promise = $http.post('/bridges/'+$scope.brname+'/netflow/del', record);
        promise.then(function(response){
            $scope.netflow = response.data.netflow;
            $scope.br.NetFlow = $scope.netflow;
        });
    };

    $scope.add_netflow = function(record){
        record.targets = record.targets.slice(0, $scope.target_count);
        var promise = $http.post('/bridges/'+$scope.brname+'/netflow/add', record);
        promise.then(function(response){
            $scope.netflow = response.data.netflow;
            $scope.br.NetFlow = $scope.netflow;
            $scope.reset();
        });
    };

    $scope.reset = function() {
        $scope.target_count = null;
        $scope.new_netflow.active_timeout = null;
        $scope.new_netflow.targets = [];
    };

}

function FlowCtrl($scope, $http){
    $scope.id = "+id";
    $scope.prio = "+priority";

    /* Predicate function to filter out empty flow tables.*/
    $scope.none_empty = function(ele) {
        if (ele.flows.length == 0)
            return false;
        else
            return true;
    };

    $scope.tables = [];

    var promise = $http.get('/bridges/tcp:127.0.0.1:6633/tables');
    promise.then(function(response) {
        $scope.tables = response.data.tables;
    });

    /* Init new_flow. */
    var init_new_flow = function() {
        var t = {};
        var names = ["priority", "cookie", "table", "match_fields",
    "actions", "counters", "duration", "idle_age", "hard_age"];
        for (var i = 0; i < names.length; i++) {
            t[names[i]] = null;
        }
        t.match_fields = {};
        var fields = ["in_port", "eth_dst", "eth_src", "eth_type",
        "vlan_vid", "vlan_pcp", "ip_dscp", "ip_ecn", "ip_proto",
        "ipv4_src", "ipv4_dst", "tp_src", "tp_dst", "icmpv4_type",
        "icmpv4_code", "arp_op", "arp_spa", "arp_tpa", "arp_sha",
        "arp_tha", "ipv6_src", "ipv6_dst", "ipv6_label",
        "icmpv6_type", "icmpv6_code", "ipv6_nd_target", "ipv6_nd_sll",
        "ipv6_nd_tll", "mpls_label", "mpls_tc", "mpls_bos", "pbb_isid",
        "tunnel_id", "ipv6_exthdr", "pbb_uca"];
        for (var i = 0; i < fields.length; i++) {
            t.match_fields[fields[i]] = null;
        }
        t.counters = {};
        t.counters["bytes"] = null;
        t.counters["packets"] = null;
        return t;
    };
    $scope.new_flow = init_new_flow();

    var table_index = function(id) {
        for (var i = 0; i < $scope.tables.length; i++) {
            if (id == $scope.tables[i].id)
                return i;
        }
        return -1;
    };

    $scope.add_flow = function(record){
        var promise = $http.post('/bridges/tcp:127.0.0.1:6633/tables/'+record.table+'/flows/add', record);
        promise.then(function(response){
            var table = response.data.table;
            var index = table_index(table.id);
            if (index >= 0)
                $scope.tables[index].flows = table.flows;
        });
        $scope.reset();
    };

    $scope.del_flow = function(record){
        var promise = $http.post('/bridges/tcp:127.0.0.1:6633/tables/'+record.table+'/flows/del', record);
        promise.then(function(response){
            var table = response.data.table;
            var index = table_index(table.id);
            if (index >= 0)
                $scope.tables[index].flows = table.flows;
        });
    };

    $scope.update_flow = function(record){
        var promise = $http.post('/bridges/tcp:127.0.0.1:6633/tables/'+record.table+'/flows/update', record);
        promise.then(function(response){
            var table = response.data.table;
            var index = table_index(table.id);
            if (index >= 0)
                $scope.tables[index].flows = table.flows;
        });
    };

    $scope.reset = function(){
        nullify($scope.new_flow);
    };
}
