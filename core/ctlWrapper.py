#!/usr/bin/env python

import subprocess
import os

database="tcp:127.0.0.1:6634"

prefix = "/ovs/bin/" if os.path.isfile("/ovs/bin/ovs-vsctl") \
        else "/usr/local/bin/"

def execute(commands):
    command = ['ovs-vsctl', '--db=%s' % database]
    sub = subprocess.Popen(command+commands, stderr=subprocess.PIPE,
            stdout=subprocess.PIPE, env={"PATH":prefix})
# FIXME where should error be handled?
    return sub.communicate()
