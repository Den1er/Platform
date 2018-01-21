#!/usr/bin/python

import os
import sys
import threading
from threading import Thread
from Queue import Queue
from threading import Lock
import random


def run_command(cmd):
    os.system(cmd)


def create_namespace(ns):
    cmd = 'ip netns add ' + ns
    run_command(cmd)


def delete_namespace_if_possible(ns):
    cmd = 'ip netns del ' + ns
    run_command(cmd)


def bridge_add(br):
    cmd = 'brctl addbr ' + br
    run_command(cmd)


def bridge_stp(br):
    cmd = 'brctl stp %s off' %(br)
    run_command(cmd)


def bridge_up(br):
    cmd = 'ip link set dev %s up' % (br)
    run_command(cmd)


def create_bridge(br):
    bridge_add(br)
    bridge_stp(br)
    bridge_up(br)


def delete_bridge(br):
    cmd = 'ip link set dev %s down' % (br)
    run_command(cmd)
    cmd = 'brctl delbr %s' % (br)
    run_command(cmd)


def create_port_pair(br, ns, br_port, ns_port):
    # create a port pair
    cmd = 'ip link add %s type veth peer name %s' % (br_port, ns_port)
    run_command(cmd)
    # attach br_port to br
    cmd = 'brctl addif %s %s' % (br, br_port)
    run_command(cmd)
    # attach ns_port to ns
    cmd = 'ip link set %s netns %s' % (ns_port, ns)
    run_command(cmd)
    # set ports up
    cmd = 'ip netns exec %s ip link set dev %s up' % (ns, ns_port)
    run_command(cmd)
    cmd = 'ip link set dev %s up' % (br_port)
    run_command(cmd)


def create_bridge_port_pair(br1, br2, br1_port, br2_port):
    # create a port pair
    cmd = 'ip link add %s type veth peer name %s' % (br1_port, br2_port)
    run_command(cmd)
    # attach br1_port to br
    cmd = 'brctl addif %s %s' % (br1, br1_port)
    run_command(cmd)
    # attach br2_port to br
    cmd = 'brctl addif %s %s' % (br2, br2_port)
    run_command(cmd)


def add_link(br, ns, br_port, ns_port):
    create_port_pair(br, ns, br_port, ns_port)


def del_link(host, intf):
    cmd = 'ip netns exec %s ip link del %s' % (host, intf)
    run_command(cmd)


def job():
    while True:
        i = queue.get()
        hNum = i % Num
        if linkState[hNum].lock.acquire(1):
            print "index %s, thread %s" % (i, threading.current_thread())
            if linkState[hNum].state == 0:
                num = random.randint(1, 2)
                cmd = 'ip link set dev h%dp%d up' % (hNum + 1, num)
                run_command(cmd)
                linkState[hNum].state = num
            elif linkState[hNum].state == 1:
                cmd = 'ip link set dev h%dp1 up' % (hNum + 1)
                run_command(cmd)
                linkState[hNum].state = 0
            elif linkState[hNum].state == 2:
                cmd = 'ip link set dev h%dp2 up' % (hNum + 1)
                run_command(cmd)
                linkState[hNum].state = 0

            linkState[hNum].lock.release()
            queue.task_done()


def ini_job():
    while not queueIni.empty():
        i = queueIni.get()
        
        create_port_pair('hbr' + str(i + 1), 'h' + str(i + 1), 'hbr' + str(i + 1) + 'p0', 'h' + str(i + 1) + 'p0')
        create_bridge_port_pair('sbr1', 'hbr' + str(i + 1), 'sbr1p' + str(i + 1), 'h' + str(i + 1) + 'p1')
        create_bridge_port_pair('sbr2', 'hbr' + str(i + 1), 'sbr2p' + str(i + 1), 'h' + str(i + 1) + 'p2')
        
        queueIni.task_done()

class ns():
    def __init__(self, state):
        self.state = state
        self.lock = Lock()

    def changeState(self, state):
        self.state = state


queue = Queue()
queueIni = Queue()
Num = 100

if __name__ == '__main__':
    if os.geteuid() != 0:
        print >> sys.stderr, 'should run in root.'
        sys.exit(1)

    # del two sats
    delete_namespace_if_possible('sat1')
    delete_namespace_if_possible('sat2')

    # del two brs
    delete_bridge('sbr1')
    delete_bridge('sbr2')

    # create two sats
    create_namespace('sat1')
    create_namespace('sat2')

    # create two brs
    create_bridge('sbr1')
    create_bridge('sbr2')

    # create sat-br pairs
    create_port_pair('sbr1', 'sat1', 'sbr1p0', 'sat1p0')
    create_port_pair('sbr2', 'sat2', 'sbr2p0', 'sat2p0')

    # delete and create 1000 host
    for i in range(Num):
        delete_namespace_if_possible('h' + str(i + 1))

    for i in range(Num):
        create_namespace('h' + str(i + 1))

    # delete and create 1000 hbr
    for i in range(Num):
        delete_bridge('hbr' + str(i + 1))

    for i in range(Num):
        create_bridge('hbr' + str(i + 1))
    """
    # create host-br pairs
    for i in range(Num):
        create_port_pair('hbr' + str(i + 1), 'h' + str(i + 1), 'hbr' + str(i + 1) + 'p0', 'h' + str(i + 1) + 'p0')

    # create br-br pairs
    for i in range(Num):
        create_bridge_port_pair('sbr1', 'hbr' + str(i + 1), 'sbr1p' + str(i + 1), 'h' + str(i + 1) + 'p1')
        create_bridge_port_pair('sbr2', 'hbr' + str(i + 1), 'sbr2p' + str(i + 1), 'h' + str(i + 1) + 'p2')
    """
    for i in range(Num):
        queueIni.put(i)

    for i in range(10):
        t = Thread(target=ini_job)
        t.daemon = True
        t.start()

    linkState = []

    for i in range(Num):
        linkState.append(ns(0))

    for i in range(10):
        t = Thread(target=job)
        t.daemon = True
        t.start()

    for i in range(10000):
        queue.put(i)

    queue.join()
