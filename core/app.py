#!/usr/bin/env python

import web
import ovsdb
import simplejson as json
import ofctrl

urls = (
    '/', 'Index',
# All Bridges
    '/bridges', 'Bridges',
    '/bridges/add', 'Bridges',
# A single Bridge
    '/bridges/(\w+)', 'Bridge',
    '/bridges/(\w+)/(update|del)', 'Bridge',
# Controllers
    '/bridges/(\w+)/controllers', 'Controller',
    '/bridges/(\w+)/controllers/(update|del|add)', 'Controller',
# Normal Ports
    '/bridges/(\w+)/ports', 'Ports',
    '/bridges/(\w+)/ports/(\w+)/(update|del|add)', 'Ports',
# Mirrors
    '/bridges/(\w+)/mirrors', 'Mirror',
    '/bridges/(\w+)/mirrors/(\w+)/(update|del|add)', 'Mirror',
# NetFlow
    '/bridges/(\w+)/netflow', 'NetFlow',
    '/bridges/(\w+)/netflow/(update|del|add)', 'NetFlow',
# sFlow
    '/bridges/(\w+)/sflow', 'sFlow',
    '/bridges/(\w+)/sflow/(update|del|add)', 'sFlow',
# Queue
    '/bridges/(\w+)/queues', 'Queues',
    '/bridges/(\w+)/queues/add', 'Queues',
    '/bridges/(\w+)/queues/(\w{8})/(update|del)', 'Queue',
# Qos
    '/bridges/(\w+)/qos', 'QoSes',
    '/bridges/(\w+)/qos/add', 'QoSes',
    '/bridges/(\w+)/qos/(\w{8})/(update|del)', 'QoS',
# Flows
    '/bridges/([\w:.]+)/tables', 'Tables',
    '/bridges/([\w:.]+)/tables/(\d+)/flows', 'Flows',
    '/bridges/([\w:.]+)/tables/(\d+)/flows/(update|add|del)', 'Flows',
)

class Index(object):
    def GET(self):
        # redirect to layout template
        raise web.seeother("/index.html")

class Bridges(object):
    def GET(self):
        """
        GET /bridges
        """
        return ovsdb.fast_get_bridges()

    def POST(self):
        """
        POST /bridges/add?name=br0
        """
        getInput = web.input()
        # TODO, elaborate add_bridge
        return ovsdb.add_bridge(str(getInput.name))

class Bridge(object):
    def GET(self, name):
        """
        GET /bridges/br0
        """
        return ovsdb.get_bridge(name)

    def POST(self, name, op):
        """
        POST /bridges/br0/update
        POST /bridges/br0/del
        """
        data = web.data()
        if op == "update":
            # TODO, elaborate update_bridge
            return ovsdb.update_bridge(name, data)
        elif op == "del":
            # TODO, elaborate del_bridge
            return ovsdb.del_bridge(name)

class Controller(object):
    def GET(self, name):
        """
        GET /bridges/br0/controllers
        """
        return ovsdb.get_controllers(name)

    def POST(self, name, op):
        """
        POST /bridges/br0/controllers/update
        POST /bridges/br0/controllers/add
        POST /bridges/br0/controllers/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_controller(name, data)
        elif op == "del":
            return ovsdb.del_controller(name, data)
        elif op == "add":
            return ovsdb.add_controller(name, data)

class Ports(object):
    def GET(self, brname):
        """
        GET /bridges/br0/Ports
        """
        return ovsdb.get_ports(brname)

    def POST(self, brname, portname, op):
        """
        POST /bridges/br0/ports/eth0/update
        POST /bridges/br0/ports/eth0/add
        POST /bridges/br0/ports/eth0/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_port(brname, data)
        elif op == "del":
            return ovsdb.del_port(brname, data)
        elif op == "add":
            return ovsdb.add_port(brname, data)

class Mirror(object):
    def GET(self, brname):
        """
        GET /bridges/br0/mirrors
        """
        return ovsdb.get_mirrors(brname)

    def POST(self, brname, mirrorname, op):
        """
        POST /bridges/br0/mirrors/M1/update
        POST /bridges/br0/mirrors/M1/add
        POST /bridges/br0/mirrors/M1/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_mirror(brname, data)
        elif op == "del":
            return ovsdb.del_mirror(brname, data)
        elif op == "add":
            return ovsdb.add_mirror(brname, data)

class NetFlow(object):
    def GET(self, brname):
        """
        GET /bridges/br0/netflow
        """
        return ovsdb.get_netflows(brname)

    def POST(self, brname, op):
        """
        POST /bridges/br0/netflow/update
        POST /bridges/br0/netflow/add
        POST /bridges/br0/netflow/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_netflow(brname, data)
        elif op == "del":
            return ovsdb.del_netflow(brname, data)
        elif op == "add":
            return ovsdb.add_netflow(brname, data)

class sFlow(object):
    def GET(self, brname):
        """
        GET /bridges/br0/sflow
        """
        return ovsdb.get_sflow(brname)

    def POST(self, brname, op):
        """
        POST /bridges/br0/sflow/update
        POST /bridges/br0/sflow/add
        POST /bridges/br0/sflow/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_sflow(brname, data)
        elif op == "del":
            return ovsdb.del_sflow(brname, data)
        elif op == "add":
            return ovsdb.add_sflow(brname, data)

class Queues(object):
    def GET(self, brname):
        """
        GET /bridges/br0/queues
        """
        return ovsdb.get_queues()

    def POST(self, brname):
        """
        POST /bridges/br0/queues/add
        """
        data = web.data()
        return ovsdb.add_queue(data)

class Queue(object):
    def GET(self):
        pass

    def POST(self, brname, uuid, op):
        """
        POST /bridges/br0/queues/00000000/update
        POST /bridges/br0/queues/00000000/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_queue(data)
        elif op == "del":
            return ovsdb.del_queue(data)

class QoSes(object):
    def GET(self, brname):
        """
        GET /bridges/br0/qos
        """
        return ovsdb.get_all_qos()

    def POST(self, brname):
        """
        POST /bridges/br0/qos/add
        """
        data = web.data()
        return ovsdb.add_qos(data)

class QoS(object):
    def GET(self):
        pass

    def POST(self, brname, uuid, op):
        """
        POST /bridges/br0/qos/00000000/update
        POST /bridges/br0/qos/00000000/del
        """
        data = web.data()
        if op == "update":
            return ovsdb.update_qos(data)
        elif op == "del":
            return ovsdb.del_qos(data)

class Tables():
    def GET(self, brname):
        """
        GET /bridges/br0/tables
        """
        wrapper = ofctrl.SimpleCtrl(brname)
        return wrapper.get_tables()

class Flows():
    def GET(self, brname, tid):
        """
        GET /bridges/br0/tables/0/flows
        """
        wrapper = ofctrl.SimpleCtrl(brname)
        return wrapper.get_flows(int(tid))

    def POST(self, brname, tid, op):
        """
        POST /bridges/br0/tables/0/flows/update
        POST /bridges/br0/tables/0/flows/add
        POST /bridges/br0/tables/0/flows/del
        """
        data = web.data()
        ofctl_wrapper = ofctrl.SimpleCtrl(brname)

        if op == "update":
            return ofctl_wrapper.mod_flow(data)
        elif op == "del":
            return ofctl_wrapper.del_flow(data)
        elif op == "add":
            return ofctl_wrapper.add_flow(data)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
        #if name:
            #bridge = json.loads(ovsdb.get_bridge(str(name)))
            #return self.render.bridge(bridge)
