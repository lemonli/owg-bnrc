#!/usr/bin/env python
import os
import subprocess

database="tcp:127.0.0.1:6634"

prefix = "/ovs/bin/" if os.path.isfile("/ovs/bin/ovs-vsctl") \
        else "/usr/local/bin/"

class Error(Exception):
    pass

class ProgrammingError(Error):
    def __init__(self, ret, msg):
        self.ret = ret
        self.msg = msg

class DatabaseError(Error):
    def __init__(self, ret, msg):
        self.ret = ret
        self.msg = msg

class InterfaceError(Error):
    def __init__(self, ret, msg):
        self.ret = ret
        self.msg = msg

class Cursor(object):
    def __init__(self):
        self.rowcount = -1
        self.command = ["ovsdb-client", "transact", database]
        self.rows = None
        self.index = -1
        pass

    def close(self):
        pass

    def execute(self, transact):
        child = subprocess.Popen(self.command + [transact], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if ret.find('"error"') >= 0:
            raise InterfaceError(-3, ret)
        else:
            res = eval(ret, {"false":False, "true":True})
            self.rows = res[0]["rows"]
            self.rowcount = len(self.rows)
            self.index = 0

    def fetchone(self):
        if self.rows is None:
            raise ProgrammingError(-3, "Previous call to .execute*() did not produce" + 
                    "any result set or no call was issued yet.")
        else:
            if self.index < self.rowcount:
                self.index += 1
                return self.rows[self.index - 1]
            else:
                # No more data is available
                return None

    def fetchall(self):
        if self.rows is None:
            raise ProgrammingError(-3, "Previous call to .execute*() did not produce" + 
                    " any result set or no call was issued yet.")
        else:
            return self.rows

class Connection(object):
    def __init__(self, target):
        self.cursors = []
        self.target = target
        command = ["ovs-vsctl", "--db=%s" % self.target, "-v", "show"]
        child = subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env={"PATH":prefix})
        ret, err = child.communicate()
        if err.find("database connection failed") >= 0:
            raise DatabaseError(-1, err)

    def close(self):
        for cur in self.cursors:
            del cur

    def commit(self):
        pass

    def cursor(self):
        cur = Cursor()
        self.cursors.append(cur)
        return cur

def connect(target=database):
    return Connection(target)

if __name__ == '__main__':
    try:
        con = connect()
    except DatabaseError as e:
        print "Database connection failed:\n%s" % e.msg
    else:
        try:
            cur = con.cursor()
            cur.execute('["Open_vSwitch", {"op":"select", "table":"Bridge", "where":[["name", "==", "br0"]]}]')
        except ProgrammingError as e:
            print "ProgrammingError:%d, %s" % (e.ret, e.msg)
        except InterfaceError as e:
            print "InterfaceError:%d, %s" % (e.ret, e.msg)
