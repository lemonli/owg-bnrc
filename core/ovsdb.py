#!/usr/bin/python
import simplejson as json
import subprocess
import clientWrapper as dbclient
import ctlWrapper as vsctl

class ovsdb_uuid:
    """
    expect ['uuid', 'af749e9c-464a-4af1-a381-7bdd2ac6be45']
    """
    def __init__(self, notation):
        self.uuid = notation[1]

    @property
    def uuid(self):
        return self.uuid

class ovsdb_set:
    """
    expect ['set', []]
    """
    def __init__(self, notation):
        self.elements = []
        if _is_type_set(notation):
            for ele in notation[1]:
                if _is_type_uuid(ele):
                    self.elements.append(ovsdb_uuid(ele).uuid)
                else:
                    self.elements.append(ele)
        else:
            if _is_type_uuid(notation):
                self.elements.append(ovsdb_uuid(notation).uuid)
            else:
                self.elements.append(notation)

    @property
    def elements(self):
        return self.elements

class ovsdb_map:
    """
    expect ['map', []]
    """
    def __init__(self, notation):
        self.pairs = {}
        for pair in notation[1]:
            self.pairs[pair[0]] = pair[1][1] if _is_type_uuid(pair[1]) else pair[1]

    @property
    def pairs(self):
        return self.pairs

class target:
    """
    expect 'ptcp:[6633][:192.168.1.1]' or 'tcp:192.168.1.1[:80]'
    """
    def __init__(self, con):
        self.con = con.split(":")
        self._ip = None
        self._port = None
        self._protocol = None
        for x in self.con:
            if x.isalpha():
                self._protocol = x
            elif x.isdigit():
                self._port = int(x)
            elif x:
                self._ip = x

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def protocol(self):
        return self._protocol

def _is_type_set(column):
    return isinstance(column, list) and column[0] == 'set'

def _is_type_map(column):
    return isinstance(column, list) and column[0] == 'map'

def _is_type_uuid(column):
    return isinstance(column, list) and column[0] == 'uuid'

def _record_to_response(record, column):
    if _is_type_set(record[column]):
        if record[column][1]:
            return record[column][1]
        else:
            return None
    else:
        if _is_type_uuid(record[column]):
            return record[column][1]
        else:
            return record[column]

def _iface_record_helper(uuid):
    con = dbclient.connect()
    cur = con.cursor()
    transact = '["Open_vSwitch", {"op":"select", "table":"Port", \
            "where":[["_uuid", "==", ["uuid", "%s"]]]}]'\
            % uuid
    cur.execute(transact)
    port_record = cur.fetchone()
    # to get Interface record
    # FIXME assuming one-to-one mapping between iface and port
    iface_uuid = ovsdb_uuid(port_record["interfaces"]).uuid
    transact = '["Open_vSwitch", {"op":"select", "table":"Interface", \
            "where":[["_uuid", "==", ["uuid", "%s"]]]}]'\
            % iface_uuid
    cur.execute(transact)
    iface_record = cur.fetchone()
    return port_record, iface_record
 
def get_bridges():
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bridges"] = []
            cur = con.cursor()
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[]}]'
            cur.execute(transact)
            for record in cur.fetchall():
                response["bridges"].append(json.loads(_get_bridge(record)))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def fast_get_bridges():
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bridges"] = []
            cur = con.cursor()
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[]}]'
            cur.execute(transact)
            for record in cur.fetchall():
                response["bridges"].append(json.loads(_fast_get_bridge(record)))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def _fast_get_bridge(record):
    """
    Return a concise bridge JSON.
    """
    response = {}
    response["name"] = record["name"]
    response["datapath_id"] = _record_to_response(record, "datapath_id")
    response["fail_mode"] = _record_to_response(record, "fail_mode")
    response["protocols"] = _record_to_response(record, "protocols")
    response["stp_config"] = {}
    other = ovsdb_map(record["other_config"]).pairs
    response["stp_config"]["stp_enable"] = _record_to_response(record, \
            "stp_enable")

    if "datapath_id" in other:
        response["datapath_id"] = other["datapath_id"]

    return json.dumps(response)

def update_bridge(brname, data):
    new_br = json.loads(data)
    commands = ['--', 'set', 'Bridge', new_br['name']]
    nullify = []

    commands.extend(['other_config:datapath_id={id}'.format(id=new_br['datapath_id'])])

    if new_br['fail_mode']:
        commands.extend(['fail_mode={0}'.format(new_br['fail_mode'])])
    else:
        nullify.extend(['--', 'clear', 'Bridge', new_br['name'], 'fail_mode'])

    if new_br['protocols']:
        commands.extend(['protocols={0}'.format(new_br['protocols'])])
    else:
        nullify.extend(['--', 'clear', 'Bridge', new_br['name'], 'protocols'])

    commands.extend(nullify)

    ret, err = vsctl.execute(commands)
    return get_bridge(brname)

def get_all_qos():
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["qoses"] = []
            cur = con.cursor()
            transact = '["Open_vSwitch", {"op":"select", "table":"QoS", \
                    "where":[]}]'
            cur.execute(transact)
            for record in cur.fetchall():
                response["qoses"].append(json.loads(_get_qos(record)))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def _get_qos(record):
    response = {}

    response["type"] = _record_to_response(record, "type")
    response["uuid"] = _record_to_response(record, "_uuid")
    response["other_config"] = {}

    config = ovsdb_map(record["other_config"]).pairs
    response["other_config"]["max-rate"] = int(config["max-rate"]) \
            if "max-rate" in config else None

    queues = ovsdb_map(record["queues"]).pairs
    response["queues"] = queues.values()

    return json.dumps(response)

def add_qos(data):
    new_qos = json.loads(data)
    commands = ['create', 'QoS']

    commands.extend(['type=%s' % new_qos['type']])

    queues = ''
    cnt = 0
    for uuid in new_qos['queues']:
        queues += '%d=%s,' % (cnt, uuid)
        cnt += 1
    if queues:
        commands.extend(['queues=%s' % queues])

    if new_qos['other_config']['max-rate']:
        commands.extend(['other_config:max-rate=%d' % new_qos['other_config']['max-rate']])

    ret, err = vsctl.execute(commands)
    return get_all_qos()

def update_qos(data):
    qos = json.loads(data)
    commands = []
    nullify = []

    if qos['type']:
        commands.extend(['type=%s' % qos['type']])
    else:
        nullify.extend(['--', 'clear', 'QoS', qos['uuid'], 'type'])

    if qos['queues']:
        queues = ''
        index = 0
        for uuid in qos['queues']:
            queues += '%s=%s,' % (index, uuid)
            index += 1
        commands.extend(['queues=%s' % queues])
    else:
        nullify.extend(['--', 'clear', 'QoS', qos['uuid'], 'queues'])

    if qos['other_config']['max-rate']:
        commands.extend(['other_config:max-rate=%d' % qos['other_config']['max-rate']])
    else:
        nullify.extend(['--', 'remove', 'QoS', qos['uuid'], 'other_config', 'max-rate'])

    if commands:
        commands = ['--', 'set', 'QoS', qos['uuid']] + commands
    commands.extend(nullify)
    ret, err = vsctl.execute(commands)
    return get_all_qos()

def del_qos(data):
    qos = json.loads(data)
    commands = ['destroy', 'QoS', qos['uuid']]
    ret, err = vsctl.execute(commands)
    return get_all_qos()

def get_queues():
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["queues"] = []
            cur = con.cursor()
            transact = '["Open_vSwitch", {"op":"select", "table":"Queue", \
                    "where":[]}]'
            cur.execute(transact)
            for record in cur.fetchall():
                response["queues"].append(json.loads(_get_queue(record)))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def _get_queue(record):
    response = {}

    response["dscp"] = _record_to_response(record, "dscp")
    response["uuid"] = _record_to_response(record, "_uuid")
    response["other_config"] = {}

    config = ovsdb_map(record["other_config"]).pairs
    response["other_config"]["min-rate"] = int(config["min-rate"]) \
            if "min-rate" in config else None
    response["other_config"]["max-rate"] = int(config["max-rate"]) \
            if "max-rate" in config else None
    response["other_config"]["burst"] = int(config["burst"]) \
            if "burst" in config else None
    response["other_config"]["priority"] = int(config["priority"]) \
            if "priority" in config else None

    return json.dumps(response)

def update_queue(data):
    nq = json.loads(data)
    commands = []
    nullify = []

    if nq['dscp']:
        commands.extend(['dscp=%d' % nq['dscp']])
    else:
        nullify.extend(['--', 'clear', 'Queue', nq['uuid'], 'dscp'])

    if nq['other_config']['min-rate']:
        commands.extend(['other_config:min-rate=%d' % nq['other_config']['min-rate']])
    else:
        nullify.extend(['--', 'remove', 'Queue', nq['uuid'], 'other_config', 'min-rate'])

    if nq['other_config']['max-rate']:
        commands.extend(['other_config:max-rate=%d' % nq['other_config']['max-rate']])
    else:
        nullify.extend(['--', 'remove', 'Queue', nq['uuid'], 'other_config', 'max-rate'])

    if nq['other_config']['burst']:
        commands.extend(['other_config:burst=%d' % nq['other_config']['burst']])
    else:
        nullify.extend(['--', 'remove', 'Queue', nq['uuid'], 'other_config', 'burst'])

    if nq['other_config']['priority']:
        commands.extend(['other_config:priority=%d' % nq['other_config']['priority']])
    else:
        nullify.extend(['--', 'remove', 'Queue', nq['uuid'], 'other_config', 'priority'])

    if commands:
        commands = ['set', 'Queue', nq['uuid']] + commands
    commands.extend(nullify)
    ret, err = vsctl.execute(commands)
    return get_queues()

def add_queue(data):
    nq = json.loads(data)
    commands = ['create', 'Queue']

    if nq['dscp']:
        commands.extend(['dscp=%d' % nq['dscp']])

    if nq['other_config']['min-rate']:
        commands.extend(['other_config:min-rate=%d' % nq['other_config']['min-rate']])

    if nq['other_config']['max-rate']:
        commands.extend(['other_config:max-rate=%d' % nq['other_config']['max-rate']])

    if nq['other_config']['burst']:
        commands.extend(['other_config:burst=%d' % nq['other_config']['burst']])

    if nq['other_config']['priority']:
        commands.extend(['other_config:priority=%d' % nq['other_config']['priority']])

    ret, err = vsctl.execute(commands)
    return get_queues()

def del_queue(data):
    q = json.loads(data)
    commands = ['destroy', 'Queue', q['uuid']]
    ret, err = vsctl.execute(commands)
    return get_queues()

def get_bonds(brname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bonds"] = []
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]'\
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                response["ports"] += json.loads(
                        _get_logical_ports(ovsdb_set(records).elements, \
                                "pica8_lag"))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def get_tunnels(brname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bonds"] = []
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]'\
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                response["ports"] += json.loads(
                        _get_logical_ports(ovsdb_set(records).elements, \
                                "pica8_gre"))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def get_bridge(brname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bridge"] = None
            cur = con.cursor()
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]]}]' % brname
            cur.execute(transact)
            record = cur.fetchone()
            if record:
                response["bridge"] = json.loads(_get_bridge(record))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def get_bond(brname, bondname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["bond"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                for uuid in ovsdb_set(records).elements:
                    transact = '["Open_vSwitch", {"op":"select", \
                            "table":"Port", \
                            "where":[["_uuid", "==", ["uuid", "%s"]],\
                            ["name", "==", "%s"]]}]' % (uuid, bondname)
                    cur.execute(transact)
                    record = cur.fetchone()
                    if record:
                        response["bond"] = json.loads(
                                _get_logical_port(uuid, "pica8_lag"))
                        break
        except InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        #DEBUG
        return json.dumps(response, indent=' '*2)

def get_tunnel(brname, tunnelname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["tunnel"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                for uuid in ovsdb_set(records).elements:
                    transact = '["Open_vSwitch", {"op":"select", \
                            "table":"Port", \
                            "where":[["_uuid", "==", ["uuid", "%s"]],\
                            ["name", "==", "%s"]]}]' % (uuid, tunnelname)
                    cur.execute(transact)
                    record = cur.fetchone()
                    if record:
                        response["tunnel"] = json.loads(
                                _get_logical_port(uuid, "pica8_gre"))
                        break
        except InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        #DEBUG
        return json.dumps(response, indent=' '*2)

def _get_bridge(record):
    """
    Caller provides this function with a record. So always assumes this
    function will succeed.
    """
    response = {}
    controller_uuids = ovsdb_set(record["controller"])
    port_uuids = ovsdb_set(record["ports"])
    sflow_uuid = ovsdb_set(record["sflow"])
    netflow_uuid = ovsdb_set(record["netflow"])
    mirror_uuids = ovsdb_set(record["mirrors"])
    response["name"] = record["name"]
    response["datapath_id"] = _record_to_response(record, "datapath_id")
    response["fail_mode"] = _record_to_response(record, "fail_mode")
    response["protocols"] = _record_to_response(record, "protocols")
    response["flood_vlans"] = _record_to_response(record, "flood_vlans")
    response["controller"] = json.loads(_get_controllers(controller_uuids.\
            elements))

    response.update(_get_all_ports(port_uuids.elements))

    response["sFlow"] = json.loads(_get_sflow(sflow_uuid.elements))
    response["NetFlow"] = json.loads(_get_netflow(netflow_uuid.elements))
    response["Mirrors"] = json.loads(_get_mirrors(mirror_uuids.elements))
    response["stp_config"] = {}
    other = ovsdb_map(record["other_config"]).pairs
    response["stp_config"]["stp_enable"] = _record_to_response(record, \
            "stp_enable")
    response["stp_config"]["stp-system-id"] = other["stp-system-id"] \
            if "stp-system-id" in other else None
    response["stp_config"]["stp-priority"] = other["stp-priority"] \
            if "stp-priority" in other else None
    response["stp_config"]["stp-hello-time"] = other["stp-hello-time"] \
            if "stp-priority" in other else None
    response["stp_config"]["stp-max-age"] = other["stp-max-age"] \
            if "stp-max-age" in other else None
    response["stp_config"]["stp-forward-delay"] = other["stp-forward-delay"] \
            if "stp-forward-delay" in other else None
    response["status"] = {}
    status = ovsdb_map(record["status"]).pairs
    response["status"]["stp_bridge_id"] = status["stp_bridge_id"] \
            if "stp_bridge_id" in status else None
    response["status"]["stp_designated_root"] = status["stp_designated_root"]\
            if "stp_designated_root" in status else None
    response["status"]["stp_root_path_cost"] = status["stp_root_path_cost"] \
            if "stp_root_path_cost" in status else None
    response["other"] = {}
    response["other"]["forward-bpdu"] = other["forward-bpdu"] \
            if "forward-bpdu" in other else None

    if "datapath_id" in other:
        response["datapath_id"] = other["datapath_id"]

    return json.dumps(response)

def _get_sflow(uuids):
    response = {}
    for uuid in uuids:
        con = dbclient.connect()
        cur = con.cursor()
        transact = '["Open_vSwitch", {"op":"select", "table":"sFlow", \
                "where":[["_uuid", "==", ["uuid", "%s"]]]}]'\
                % uuid
        cur.execute(transact)
        record = cur.fetchone()
        response["agent"] = _record_to_response(record, "agent")
        response["header"] = _record_to_response(record, "header")
        response["polling"] = _record_to_response(record, "polling")
        response["sampling"] = _record_to_response(record, "sampling")
        response["targets"] = []
        for tar in record["targets"].split(","):
            if tar:
                t = target(tar)
                response["targets"].append(dict(ip=t.ip, port=t.port))
    return json.dumps(response)

def _get_netflow(uuids):
    response = {}
    for uuid in uuids:
        con = dbclient.connect()
        cur = con.cursor()
        transact = '["Open_vSwitch", {"op":"select", "table":"NetFlow", \
                "where":[["_uuid", "==", ["uuid", "%s"]]]}]'\
                % uuid
        cur.execute(transact)
        record = cur.fetchone()
        response["active_timeout"] = _record_to_response(record, "active_timeout")
        response["targets"] = []
        for tar in record["targets"].split(","):
            if tar:
                t = target(tar)
                response["targets"].append(dict(ip=t.ip, port=t.port))
    return json.dumps(response)

def _get_mirrors(uuids):
    response = []
    for uuid in uuids:
        response.append(json.loads(_get_mirror(uuid)))
    return json.dumps(response)

def _get_mirror(uuid):
    response = {}
    con = dbclient.connect()
    cur = con.cursor()
    transact = '["Open_vSwitch", {"op":"select", "table":"Mirror", \
            "where":[["_uuid", "==", ["uuid", "%s"]]]}]'\
            % uuid
    cur.execute(transact)
    for record in cur.fetchall():
        response["name"] = _record_to_response(record, "name")
        response["select_all"] = _record_to_response(record, "select_all")
        response["select_src_port"] = []
        for port in ovsdb_set(record["select_src_port"]).elements:
            response["select_src_port"].append(port)
        response["select_dst_port"] = []
        for port in ovsdb_set(record["select_dst_port"]).elements:
            response["select_dst_port"].append(port)
        response["select_vlan"] = []
        for vlan in ovsdb_set(record["select_vlan"]).elements:
            response["select_vlan"].append(vlan)
        response["statistics"] = {}
        response["statistics"]["tx_bytes"] = 0
        response["statistics"]["tx_packets"] = 0
        for key, val in ovsdb_map(record["statistics"]).pairs.iteritems():
            response["statistics"][key] = val
        response["output_port"] = _record_to_response(record, "output_port")
        response["output_vlan"] = _record_to_response(record, "output_vlan")
# replace port uuid with port name
    tmp = []
    for uuid in response["select_src_port"]:
        tmp = [json.loads(_get_port(uuid))["name"] \
                for uuid in response["select_src_port"]]
    response["select_src_port"] = tmp
    tmp = []
    for uuid in response["select_dst_port"]:
        tmp = [json.loads(_get_port(uuid))["name"]\
                for uuid in response["select_dst_port"]]
    response["select_dst_port"] = tmp
    tmp = []
    if response["output_port"]:
        tmp = json.loads(_get_port(response["output_port"]))["name"]
    response["output_port"] = tmp
    return json.dumps(response)

def get_controllers(brname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["controllers"] = []
            transact = '["Open_vSwitch", {"op":"select","table":"Bridge",\
                    "where":[["name","==","%s"]],"columns":["controller"]}]'\
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["controller"]
                response["controllers"] += json.loads(
                        _get_controllers(ovsdb_set(records).elements))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def _get_controllers(uuids=[]):
    # caller should guarantee that bridge name is in the database
    response = []
    for uuid in uuids:
        response.append(_get_controller(uuid))
    return json.dumps(response)
   
def _get_controller(uuid):
    response = {}

    con = dbclient.connect()
    cur = con.cursor()
    transact = '["Open_vSwitch", {"op":"select", "table":"Controller", \
            "where":[["_uuid", "==", ["uuid", "%s"]]]}]'  % uuid
    cur.execute(transact)
    record = cur.fetchone()
    # refer to documentation for the controller object JSON schema
    t = target(record["target"])
    response["uuid"] = _record_to_response(record, "_uuid")
    response["ip"] = t.ip
    response["port"] = t.port
    response["protocol"] = t.protocol
    response["connection_mode"] = _record_to_response(record, \
            "connection_mode")
    response["max_backoff"] = _record_to_response(record, "max_backoff")
    response["inactivity_probe"] = _record_to_response(record, \
            "inactivity_probe")
    response["enable_async_messages"] = _record_to_response(record, \
            "enable_async_messages")
    response["controller_rate_limit"] = _record_to_response(record, \
            "controller_rate_limit")
    response["controller_burst_limit"] = _record_to_response(record, \
            "controller_burst_limit")
    response["in_band"] = {}
    response["in_band"]["local_ip"] = _record_to_response(record, "local_ip")
    response["in_band"]["local_netmask"] = _record_to_response(record, \
            "local_netmask")
    response["in_band"]["local_gateway"] = _record_to_response(record, \
            "local_gateway")
    response["is_connected"] = record["is_connected"]
    response["role"] = _record_to_response(record, "role")
    response["status"] = {}
    status = ovsdb_map(record["status"])
    response["status"]["state"] = status.pairs.get("state", None)
    return response

def get_ports(brname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["ports"] = []
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]'\
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                response["ports"] += json.loads(
                        _get_ports(ovsdb_set(records).elements))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def get_port(brname, portname):
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["port"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["ports"]}]'\
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["ports"]
                for uuid in ovsdb_set(records).elements:
                    transact = '["Open_vSwitch", {"op":"select", \
                            "table":"Port", \
                            "where":[["_uuid", "==", ["uuid", "%s"]], \
                            ["name", "==", "%s"]]}]' % (uuid, portname)
                    cur.execute(transact)
                    record = cur.fetchone()
                    if record:
                        response["port"] = json.loads(_get_port(uuid))
                        break
        except InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        #DEBUG
        return json.dumps(response, indent=' '*2)

def _get_ports(uuids=[]):
    response = []
    for uuid in uuids:
        port = _get_port(uuid)
        # _get_port should return "{}" if uuid is not a physical port
        if json.loads(port):
            response.append(json.loads(port))
    return json.dumps(response)

def _get_port(uuid):
    response = {}

    port_record, iface_record = _iface_record_helper(uuid)

    if not iface_record["type"] or iface_record["type"] == "system":
        response["name"] = port_record["name"]
        response["mac"] = _record_to_response(port_record, "mac")
        response["qos"] = _record_to_response(port_record, "qos")
        response["ofport"] = iface_record["ofport"]
        response["type"] = "phy"
        response["vlan_config"] = {}
        response["vlan_config"]["vlan_mode"] =\
                _record_to_response(port_record, "vlan_mode")
        response["vlan_config"]["tag"] =\
                _record_to_response(port_record, "tag")
        response["vlan_config"]["trunks"] =\
                _record_to_response(port_record, "trunks")
        response["status"] = {}
        # Status
        status = ovsdb_map(port_record["status"]).pairs
        response["status"]["stp_port_id"] = status["stp_port_id"]\
                if "stp_port_id" in status else None 
        response["status"]["stp_state"] = status["stp_state"]\
                if "stp_state" in status else None 
        response["status"]["stp_sec_in_state"] = status["stp_sec_in_state"]\
                if "stp_sec_in_state" in status else None 
        response["status"]["stp_role"] = status["stp_role"]\
                if "stp_role" in status else None 
        response["admin_state"] = _record_to_response(iface_record,
                "admin_state")
        response["link_state"] = _record_to_response(iface_record,\
                "link_state") 
        response["duplex"] = _record_to_response(iface_record, "duplex")
        response["mtu"] = _record_to_response(iface_record, "mtu")
        response["options"] = {}
        # Options
        options = ovsdb_map(iface_record["options"]).pairs
        response["options"]["link_speed"] = options["link_speed"]\
                if "link_speed" in options else None
        # Statistics
        response["statistics"] = {}
        response["statistics"]["counters"] = {}
        response["statistics"]["receive_errors"] = {}
        response["statistics"]["transmit_errors"] = {}
        response["statistics"]["stp_counters"] = {}
        statistics = ovsdb_map(iface_record["statistics"]).pairs
# counter
        response["statistics"]["counters"]["rx_packets"] = \
                statistics["rx_packets"]
        response["statistics"]["counters"]["rx_bytes"] = \
                statistics["rx_bytes"]
        response["statistics"]["counters"]["tx_packets"] = \
                statistics["tx_packets"]
        response["statistics"]["counters"]["tx_bytes"] = \
                statistics["tx_bytes"]
# receive_errors
        response["statistics"]["receive_errors"]["rx_dropped"] = \
                statistics["rx_dropped"]
        response["statistics"]["receive_errors"]["rx_frame_err"] = \
                statistics["rx_frame_err"]
        response["statistics"]["receive_errors"]["rx_over_err"] = \
                statistics["rx_over_err"]
        response["statistics"]["receive_errors"]["rx_crc_err"] = \
                statistics["rx_crc_err"]
        response["statistics"]["receive_errors"]["rx_errors"] = \
                statistics["rx_errors"]
# transmit_errors
        response["statistics"]["transmit_errors"]["tx_dropped"] = \
                statistics["tx_dropped"]
        response["statistics"]["transmit_errors"]["collisions"] = \
                statistics["collisions"]
        response["statistics"]["transmit_errors"]["tx_errors"] = \
                statistics["tx_errors"]
# stp counters
        stp_counter = ovsdb_map(port_record["statistics"]).pairs
        response["statistics"]["stp_counters"]["stp_tx_count"] = \
                stp_counter["stp_tx_count"] \
                if "stp_tx_count" in stp_counter else None
        response["statistics"]["stp_counters"]["stp_rx_count"] = \
                stp_counter["stp_rx_count"] \
                if "stp_rx_count" in stp_counter else None
        response["statistics"]["stp_counters"]["stp_error_count"] = \
                stp_counter["stp_error_count"] \
                if "stp_error_count" in stp_counter else None

    return json.dumps(response)

def update_port(brname, data):
    port = json.loads(data)
    commands = []
    if port["vlan_config"]["vlan_mode"] == 'access':
        commands = ['--', 'set', 'Port', port['name'], 'vlan_mode=access',
                '--', 'set', 'Port', port['name'], 'tag=%d' % \
                        port['vlan_config']['tag']]
    elif port["vlan_config"]["vlan_mode"] == 'trunk':
        commands = ['--', 'set', 'Port', port['name'], 'vlan_mode=trunk',
                '--', 'set', 'Port', port['name'], 'trunks=%s' % \
                        str(port['vlan_config']['trunks'])]

    if port["options"]["link_speed"] > 0:
# TODO, set link speed here
# options:link_speed=1G
        pass

    if port["qos"]:
        commands.extend(['--', 'set', 'Port', port['name'], 'qos=%s' %
            port['qos']])
    else:
        commands.extend(['--', 'clear', 'Port', port['name'], 'qos'])

    ret, err = vsctl.execute(commands)
    return get_ports(brname)

def del_port(brname, data):
    port = json.loads(data)
    commands = ['del-port', brname, port["name"]]
    ret, err = vsctl.execute(commands)
    return get_ports(brname)

def add_port(brname, data):
    port = json.loads(data)
    commands = ['--', 'add-port', brname, port["name"], '--',
            'set', 'Interface', port["name"], 'type=system']

    vlan_config = []

    if port['vlan_config']['vlan_mode'] == 'access':
        vlan_config = ['--', 'set', 'Port', port["name"], 'vlan_mode=access',
                '--', 'set', 'Port', port["name"],
                'tag=%d' % port['vlan_config']['tag']]
    elif port['vlan_config']['vlan_mode'] == 'trunk':
        vlan_config = ['--', 'set', 'Port', port["name"], 'vlan_mode=trunk',
                '--', 'set', 'Port', port["name"],
                'trunks=%s' % str(port['vlan_config']['trunks'])]
    commands.extend(vlan_config)
    ret, err = vsctl.execute(commands)
    return get_ports(brname)

def _get_logical_ports(uuids, type):
    response = []
    for uuid in uuids:
        port = _get_logical_port(uuid, type)
        # _get_port should return "{}" if uuid is not a physical port
        if json.loads(port):
            response.append(json.loads(port))
    return json.dumps(response)

def _get_logical_port(uuid, type):
    response = {}
    port_record, iface_record = _iface_record_helper(uuid)

    if iface_record["type"] == type:
        response["name"] = port_record["name"]
        response["ofport"] = iface_record["ofport"]
        response["type"] = type
        response["vlan_config"] = {}
        response["vlan_config"]["vlan_mode"] =\
                _record_to_response(port_record, "vlan_mode")
        response["vlan_config"]["tag"] =\
                _record_to_response(port_record, "tag")
        response["vlan_config"]["trunks"] =\
                _record_to_response(port_record, "trunks")
        response["options"] = {}
        # Options
        options = ovsdb_map(iface_record["options"]).pairs
        response["options"]["lag_type"] = options["lag_type"]\
                if "lag_type" in options else None
        response["options"]["members"] = options["members"]\
                if "members" in options else None
        response["options"]["lacp-system-id"] = options["lacp-system-id"]\
                if "lacp-system-id" in options else None
        response["options"]["lacp-system-priority"] = \
                options["lacp-system-priority"] \
                if "lacp-system-priority" in options else None
        response["options"]["lacp-time"] = options["lacp-time"]\
                if "lacp-time" in options else None
        response["options"]["lacp-mode"] = options["lacp-mode"]\
                if "lacp-mode" in options else None
        response["options"]["lacp-port-id"] = options["lacp-port-id"]\
                if "lacp-port-id" in options else None
        response["options"]["lacp-port-priority"] = \
                options["lacp-port-priority"] \
                if "lacp-port-priority" in options else None
        response["options"]["lacp-aggregation-key"] = \
                options["lacp-aggregation-key"] \
                if "lacp-aggregation-key" in options else None
        response["options"]["remote_ip"] = options["remote_ip"]\
                if "remote_ip" in options else None
        response["options"]["local_ip"] = options["local_ip"]\
                if "local_ip" in options else None
        response["options"]["vlan"] = options["vlan"]\
                if "vlan" in options else None
        response["options"]["src_mac"] = options["src_mac"]\
                if "src_mac" in options else None
        response["options"]["dst_mac"] = options["dst_mac"]\
                if "dst_mac" in options else None
        response["options"]["egress_port"] = options["egress_port"]\
                if "egress_port" in options else None

    return json.dumps(response)

def _get_all_ports(uuids=[]):
    response = {
            "ports" : [],
            "lags" : [],
            "tunnels" : []
            }

    for uuid in uuids:
        port_record, iface_record = _iface_record_helper(uuid)
        if not iface_record["type"] or iface_record["type"] == "system":
            response["ports"].append(json.loads(_get_port(uuid)))
        elif iface_record["type"] == "pica8_gre":
            response["tunnels"].append(json.loads(_get_logical_port(uuid, "pica8_gre")))
        elif iface_record["type"] == "pica8_lag":
            response["lags"].append(json.loads(_get_logical_port(uuid, "pica8_lag")))

    return response


def get_sflow(brname):
    """
    If Bridge brname doesn't have an sflow record, return None.
    """
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["sflow"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["sflow"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                record = row["sflow"]
                if record[1]:
                    response["sflow"] = json.loads(_get_sflow(ovsdb_set(record).elements))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def update_sflow(brname, data):
    sf = json.loads(data)
    commands = ['--', 'set', 'sFlow', brname]
    clear = []

    if sf['agent']:
        commands.extend(['agent=%s' % sf['agent']])
    else:
        clear.extend(['--', 'clear', 'sflow', brname, 'agent'])

    if sf['header']:
       commands.extend(['header=%d' % sf['header']])
    else:
        clear.extend(['--', 'clear', 'sflow', brname, 'header'])

    if sf['polling']:
       commands.extend(['polling=%d' % sf['polling']])
    else:
        clear.extend(['--', 'clear', 'sflow', brname, 'polling'])

    if sf['sampling']:
       commands.extend(['sampling=%d' % sf['sampling']])
    else:
        clear.extend(['--', 'clear', 'sflow', brname, 'sampling'])

    targets = ''
    for target in sf['targets']:
        targets += target['ip'] + ':' + str(target['port']) + ','
    commands.extend(['targets=%s' % ('\"' + targets + '\"')])

    commands.extend(clear)

    ret, err = vsctl.execute(commands)
    return get_sflow(brname)

def del_sflow(brname, data):
    sf = json.loads(data)
    commands = ['clear', 'Bridge', brname, 'sflow']
    ret, err = vsctl.execute(commands)
    return get_sflow(brname)

def add_sflow(brname, data):
    sf = json.loads(data)
    commands = ['--', 'set', 'Bridge', brname, 'sflow=@sf',
            '--', '--id=@sf', 'create', 'sFlow']

    if sf['agent']:
        commands.extend(['agent=%s' % sf['agent']])

    if sf['header']:
       commands.extend(['header=%d' % sf['header']])

    if sf['polling']:
       commands.extend(['polling=%d' % sf['polling']])

    if sf['sampling']:
       commands.extend(['sampling=%d' % sf['sampling']])

    targets = ''
    for target in sf['targets']:
        targets += target['ip'] + ':' + str(target['port']) + ','
    commands.extend(['targets=%s' % ('\"' + targets + '\"')])

    ret, err = vsctl.execute(commands)
    print ret
    print err
    return get_sflow(brname)

def get_netflow(brname):
    """
    If Bridge brname doesn't have an newflow record, return None.
    """
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["netflow"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["netflow"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                record = row["netflow"]
                if record[1]:
                    response["netflow"] = json.loads(_get_netflow(ovsdb_set(record).elements))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def update_netflow(brname, data):
    nf = json.loads(data)
    commands = ['--', 'set', 'NetFlow', brname]

    commands.extend(['active_timeout=%d' % nf['active_timeout']])

    targets = ''
    for target in nf['targets']:
        targets += target['ip'] + ':' + str(target['port']) + ','
    commands.extend(['targets=%s' % ('\"' + targets + '\"')])

    ret, err = vsctl.execute(commands)
    return get_netflow(brname)

def del_netflow(brname, data):
    nf = json.loads(data)
    commands = ['clear', 'Bridge', brname, 'netflow']
    ret, err = vsctl.execute(commands)
    return get_netflow(brname)

def add_netflow(brname, data):
    nf = json.loads(data)
    commands = ['--', 'set', 'Bridge', brname, 'netflow=@nf',
            '--', '--id=@nf', 'create', 'NetFlow']

    commands.extend(['active_timeout=%d' % nf['active_timeout']])

    targets = ''
    for target in nf['targets']:
        targets += target['ip'] + ':' + str(target['port']) + ','
    commands.extend(['targets=%s' % ('\"' + targets + '\"')])

    ret, err = vsctl.execute(commands)
    return get_netflow(brname)

def get_mirrors(brname):
    """
    If Bridge brname doesn't contain any mirror records, return an empty list.
    """
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["mirrors"] = []
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["mirrors"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            row = cur.fetchone()
            if row:
                records = row["mirrors"]
                response["mirrors"] = json.loads(_get_mirrors(ovsdb_set(records).elements))
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        return json.dumps(response)

def get_mirror(brname, mirname):
    """
    If Bridge brname doesn't contain any mirror named mirname, return None.
    """
    response = {}
    try:
        con = dbclient.connect()
    except dbclient.DatabaseError as e:
        response["ret"] = e.ret
        response["msg"] = e.msg
        return json.dumps(response)
    else:
        try:
            response["ret"] = 0
            response["mirror"] = None
            transact = '["Open_vSwitch", {"op":"select", "table":"Bridge", \
                    "where":[["name", "==", "%s"]], "columns":["mirrors"]}]' \
                    % brname
            cur = con.cursor()
            cur.execute(transact)
            record = cur.fetchone()
            if record:
                records = record["mirrors"]
                for uuid in ovsdb_set(records).elements:
                    transact = '["Open_vSwitch", {"op":"select", "table":"Mirror", \
                        "where":[["_uuid", "==", ["uuid", "%s"]], \
                        ["name", "==", "%s"]]}]' % (uuid, mirname)
                    cur.execute(transact)
                    record = cur.fetchone()
                    if record:
                        response["mirror"] = json.loads(_get_mirror(uuid))
                        break
        except dbclient.InterfaceError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except dbclient.ProgrammingError as e:
            response["ret"] = e.ret
            response["msg"] = e.msg
        except:
            print "error"
        return json.dumps(response)

def update_mirror(brname, data):
    mirror = json.loads(data)
    commands = []
    if mirror['output_port']:
        ids = port_ids(mirror['select_src_port'],
                mirror['select_dst_port'],
                mirror['output_port'])
        commands.extend(ids)
        if not mirror['select_src_port']:
            commands.extend([
                '--', 'clear', 'Mirror', mirror['name'], 'select_src_port'])
        if not mirror['select_dst_port']:
            commands.extend([
                '--', 'clear', 'Mirror', mirror['name'], 'select_dst_port'])
        # Clear VLAN section
        commands.extend([
            '--', 'clear', 'Mirror', mirror['name'], 'select_vlan',
            '--', 'clear', 'Mirror', mirror['name'], 'output_vlan'])
        commands.extend([
            '--', 'set', 'Mirror', mirror['name']])
        if mirror['select_src_port']:
            commands.append('select_src_port=%s' %
                add_prefix(mirror['select_src_port']))
        if mirror['select_dst_port']:
            commands.append('select_dst_port=%s' %
                add_prefix(mirror['select_dst_port']))
        commands.append('output_port=%s' %
            add_prefix(mirror['output_port']))
    elif mirror['output_vlan']:
        # Clear Port section
        commands.extend([
            '--', 'clear', 'Mirror', mirror['name'], 'select_src_port',
            '--', 'clear', 'Mirror', mirror['name'], 'select_dst_port',
            '--', 'clear', 'Mirror', mirror['name'], 'output_port'])
        commands.extend([
            '--', 'set', 'Mirror', mirror['name'],
            'name=%s' % mirror['name'],
            'select_vlan=%s' % mirror['select_vlan'],
            'output_vlan=%s' % mirror['output_vlan']])

    ret, err = vsctl.execute(commands)
    return get_mirrors(brname)

def del_mirror(brname, data):
    mirror = json.loads(data)
    commands = ['--', '--id=@tmp', 'get', 'Mirror', mirror['name'],
            '--', 'remove', 'Bridge', brname, 'mirrors', '@tmp']
    ret, err = vsctl.execute(commands)
    return get_mirrors(brname)

def add_prefix(input):
    if isinstance(input, str) or isinstance(input, unicode):
        return ','.join(map(lambda x: '@'+x if x else x, input.split(',')))
    else:
        return map(lambda x: '@'+x, input)

def port_ids(*args):
    ports = set([])
    for x in args:
        if x:
            if isinstance(x, list):
                ports.update(x)
            elif isinstance(x, str) or isinstance(x, unicode):
                ports.update(x.split(','))
    return reduce(lambda x, y: x + y, map(lambda p: ['--', '--id=@%s' % p, 'get', 'Port', p], ports))

def add_mirror(brname, data):
    mirror = json.loads(data)
    commands = ['--', 'add', 'Bridge', brname, 'mirrors', '@tmp']
    if mirror['output_port']:
        ids = port_ids(mirror['select_src_port'],
                mirror['select_dst_port'],
                mirror['output_port'])
        commands.extend(ids)
        commands.extend([
            '--', '--id=@tmp', 'create', 'mirror',
            'name=%s' % mirror['name']])
        if mirror['select_src_port']:
            commands.append('select_src_port=%s' %
                add_prefix(mirror['select_src_port']))
        if mirror['select_dst_port']:
            commands.append('select_dst_port=%s' %
                add_prefix(mirror['select_dst_port']))
        commands.append('output_port=%s' %
            add_prefix(mirror['output_port']))
    elif mirror['output_vlan']:
        commands.extend([
            '--', '--id=@tmp', 'create', 'mirror',
            'name=%s' % mirror['name'],
            'select_vlan=%s' % mirror['select_vlan'],
            'output_vlan=%s' % mirror['output_vlan']])

    ret, err = vsctl.execute(commands)
    return get_mirrors(brname)

def add_bridge(br_name):
    commands = ['--', 'add-br', br_name, '--', 'set', 'Bridge', \
            br_name, 'datapath_type=system']
    ret, err = vsctl.execute(commands)
    return fast_get_bridges()

def del_bridge(br_name):
    command = ['--', 'del-br', br_name]
    ret, err = vsctl.execute(command)
    return fast_get_bridges()

def add_controller(br_name, data):
    newctrl = json.loads(data)

    if newctrl["protocol"] == 'tcp' or newctrl["protocol"] == 'ssl':
        # assume newctrl["ip"] is not None
        if not newctrl["port"]:
            newctrl["port"] = 6633
        target = ":".join([newctrl["protocol"], newctrl["ip"], str(newctrl["port"])])
    elif newctrl["protocol"] == 'ptcp' or newctrl["protocol"] == 'pssl':
        if not newctrl["port"]:
            newctrl["port"] = 6633
        # newctrl["ip"] not used
        target = ":".join([newctrl["protocol"], str(newctrl["port"])])
    target = 'target=%s' % ('\"' + target + '\"')
    commands = ['--', 'add', 'Bridge', br_name, 'controller', '@new', '--',\
            '--id=@new', 'create', 'Controller', target]

    if newctrl["connection_mode"]:
        connection_mode = 'connection_mode=%s' % newctrl["connection_mode"]
        commands.append(connection_mode)

    ret, err = vsctl.execute(commands)
    return get_controllers(br_name)

def del_controller(br_name, data):
    newctrl = json.loads(data)
    commands = ['--', 'remove', 'Bridge', br_name, 'controller', \
            newctrl["uuid"]]
    ret, err = vsctl.execute(commands)
    return get_controllers(br_name)

def update_controller(br_name, data):
    newctrl = json.loads(data)
    if newctrl["protocol"] == 'tcp' or newctrl["protocol"] == 'ssl':
        # assume newctrl["ip"] is not None
        if not newctrl["port"]:
            newctrl["port"] = 6633
        target = ":".join([newctrl["protocol"], newctrl["ip"], str(newctrl["port"])])
    elif newctrl["protocol"] == 'ptcp' or newctrl["protocol"] == 'pssl':
        if not newctrl["port"]:
            newctrl["port"] = 6633
        # newctrl["ip"] not used
        target = ":".join([newctrl["protocol"], str(newctrl["port"])])
    target = 'target=%s' % ('\"' + target + '\"')

    commands = ['--', 'set', 'Controller', newctrl["uuid"], target]

    if newctrl["connection_mode"]:
        connection_mode = 'connection_mode=%s' % newctrl["connection_mode"]
        commands.append(connection_mode)
    # TODO: more columns to set
    ret, err = vsctl.execute(commands)
    return get_controllers(br_name)

if __name__ == "__main__":
    print get_bridges()
