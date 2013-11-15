#!/usr/bin/env python

import os
import subprocess
import simplejson as json
import re

prefix = "/ovs/bin/" if os.path.isfile("/ovs/bin/ovs-vsctl") \
        else "/usr/local/bin/"

alias_ovs2st = {
        "dl_vlan": "vlan_vid",
        "dl_vlan_pcp": "vlan_pcp",
        "dl_src": "eth_src",
        "dl_dst": "eth_dst",
        "dl_type": "eth_type",
        "nw_src": "ipv4_src",
        "nw_dst": "ipv4_dst",
        "nw_proto": "ip_proto",
        "nw_tos": "ip_dsctp",
        "nw_ecn": "ip_ecn",
        "ipv6_label": "ipv6_flabel",
        "ng_target": "ipv6_nd_target",
        "nd_ssl": "ipv6_nd_ssl",
        "nd_tll": "ipv6_nd_tll",
        "tun_id": "tunnel_id",
        }

alias_st2ovs = {
        "vlan_vid": "dl_vlan",
        "vlan_pcp": "dl_vlan_pcp",
        "eth_src": "dl_src",
        "eth_dst": "dl_dst",
        "eth_type": "dl_type",
        "ipv4_src": "nw_src",
        "ipv4_dst": "nw_dst",
        "ip_proto": "nw_proto",
        "ip_dsctp": "nw_tos",
        "ip_ecn": "nw_ecn",
        "ipv6_flabel": "ipv6_label",
        "ipv6_nd_target": "ng_target",
        "ipv6_nd_ssl": "nd_ssl",
        "ipv6_nd_tll": "nd_tll",
        "tunnel_id": "tun_id",
        }

abbreviates = [ "ip", "icmp", "tcp", "udp", "arp", "rarp",
                "ipv6", "tcp6", "udp6", "icmp6" ]

class ofctlParser(object):
    def __init__(self, raw):
        self.raw = raw
        self.flow = dict(
                match_fields = {},
                counters = {},
                )

    def _preprocess(self):
        self.flow["actions"] = re.search("actions=([^ ]+)", self.raw).group(1)
        self._params = {}
        prefix = self.raw[:self.raw.find("actions")]
        pairs = re.split(", ?", prefix.strip())
        for pair in pairs:
            name, sep, value = pair.partition("=")
            if name:
                self._params[name] = value

    def convertShort(self, short):
        if short == "ip":
            self._shorthands("0x0800", None)
        if short == "icmp":
            self._shorthands("0x0800", "1")
        if short == "tcp":
            self._shorthands("0x0800", "6")
        if short == "udp":
            self._shorthands("0x0800", "17")
        if short == "arp":
            self._shorthands("0x0806", None)
        if short == "rarp":
            self._shorthands("0x0835", None)
        if short == "ipv6":
            self._shorthands("0x86dd", None)
        if short == "tcp6":
            self._shorthands("0x86dd", "6")
        if short == "udp6":
            self._shorthands("0x86dd", "17")
        if short == "icmp6":
            self._shorthands("0x86dd", "58")

    def _shorthands(self, dl_type, nw_proto):
        self.flow["match_fields"]["eth_type"] = dl_type
        if nw_proto:
            self.flow["match_fields"]["ip_proto"] = nw_proto

    @staticmethod
    def aliasForCmd(field):
        return alias_st2ovs[field] if field in alias_st2ovs else field

    def convert2json(self):
        self._preprocess()
        # Priority
        if "priority" in self._params:
            self.flow["priority"] = int(self._params["priority"])
            del self._params["priority"]
        else:
            self.flow["priority"] = 32768

        # Cookie
        self.flow["cookie"] = self._params["cookie"]
        del self._params["cookie"]

        # Table
        self.flow["table"] = self._params["table"]
        del self._params["table"]

        # Counters
        self.flow["counters"]["bytes"] = self._params["n_bytes"]
        self.flow["counters"]["packets"] = self._params["n_packets"]
        del self._params["n_bytes"]
        del self._params["n_packets"]

        # Duration
        self.flow["duration"] = self._params["duration"]
        del self._params["duration"]

        # Idel Age
        self.flow["idle_age"] = self._params["idle_age"]
        del self._params["idle_age"]

        # Hard Age
        if "hard_age" in self._params:
            self.flow["hard_age"] = self._params["hard_age"]
            del self._params["hard_age"]

        for key, val in self._params.iteritems():
            if key in abbreviates:
                self.convertShort(key)
            elif key in alias_ovs2st:
                self.flow["match_fields"][alias_ovs2st[key]] = val
            else:
                self.flow["match_fields"][key] = val

class SimpleCtrl(object):
    def __init__(self, sw):
        self.switch = sw

    def get_tables(self):
        response = {}
        tmp = [{"id":i, "flows":[]} for i in range(0, 256)]

        command = ['ovs-ofctl', 'dump-flows', self.switch]
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err:
            response["ret"] = -1
            response["msg"] = err.partition(":")[2]
        else:
            response["ret"] = 0
            for raw_flow in ret.splitlines()[1:]:
                json_flow = self._string_to_json(raw_flow)
                table_index = int(json_flow["table"])
                tmp[table_index]["flows"].append(json_flow)
            response["tables"] = filter(lambda item: True if item["flows"] else False, tmp)

        return json.dumps(response)

    def get_flows(self, tableid):
        """
        ovs-ofctl dump-flows switch
        """
        response = {}
        command = ['ovs-ofctl', 'dump-flows', self.switch]
        command.append('table=%d' % tableid)
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err:
            response["ret"] = -1
            response["msg"] = err.partition(":")[2]
        else:
            response["ret"] = 0
            response["table"] = {}
            response["table"]["id"] = tableid
            response["table"]["flows"] = []
            for raw_flow in ret.splitlines()[1:]:
                response["table"]["flows"].append(self._string_to_json(raw_flow))

        return json.dumps(response)

    def add_flow(self, data):
        """
        ovs-ofctl add-flow switch flow
        """
        flow = json.loads(data)
        response = {}
        command = ['ovs-ofctl', 'add-flow', self.switch]
        command.append("{fields},actions={actions}".format(
            fields=self._flow_json_to_string(flow),
            actions=flow["actions"]))
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err:
            response["ret"] = -1
            response["msg"] = err.partition(":")[2]
            return response
        else:
            return self.get_flows(int(flow["table"]))

    def mod_flow(self, data):
        """
        ovs-ofctl --strict mod-flows switch flow
        """
        flow = json.loads(data)
        response = {}
        command = ['ovs-ofctl', '--strict', 'mod-flows', self.switch]
        command.append("{fields},actions={actions}".format(
            fields=self._flow_json_to_string(flow),
            actions=flow["actions"]))
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err:
            response["ret"] = -1
            response["msg"] = err.partition(":")[2]
            return response
        else:
            return self.get_flows(int(flow["table"]))

    def del_flow(self, data):
        """
        ovs-ofctl --strict del-flows switch flow
        """
        flow = json.loads(data)
        response = {}
        command = ['ovs-ofctl', '--strict', 'del-flows', self.switch]
        command.append(self._flow_json_to_string(flow))
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err:
            response["ret"] = -1
            response["msg"] = err.partition(":")[2]
            return response
        else:
            return self.get_flows(int(flow["table"]))

    def _flow_json_to_string(self, flow):
        fields = []
        if flow["priority"]:
            fields.append("priority={0}".format(flow["priority"]))
        if flow["table"]:
            fields.append("table={0}".format(flow["table"]))
        fields.extend(map(lambda x:"{0}={1}".format(ofctlParser.aliasForCmd(x[0]),x[1]),
                filter(lambda x: True if x[1] else False, flow["match_fields"].items())))

        return ",".join(fields)

    def _string_to_json(self, raw):
        parser = ofctlParser(raw)
        parser.convert2json()
        return parser.flow

if __name__ == "__main__":
    myctrl = SimpleCtrl("tcp:127.0.0.1:6633")
    data = {
      "idle_age": "26266",
      "actions": "drop",
      "priority": 32768,
      "match_fields": {
        "eth_src": "00:0a:e4:25:6b:b0",
        "in_port": "LOCAL",
        "vlan_vid": "9"
      },
      "cookie": "0x0",
      "duration": "26266.455s",
      "table": "0",
      "counters": {
        "packets": "0",
        "bytes": "0"
      }
    }

    print myctrl.get_flows()
    #print myctrl.del_flow(data)
    #flows = json.loads(myctrl.get_flows())["flows"]
    #for flow in flows:
        #print myctrl._flow_json_to_string(flow)
