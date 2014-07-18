# Zabbix Generic Discovery

## What
Zabbix Generic Discovery extends default zabbix discovery with use of API and external
helper python application. Example (reference implementation) application that can be monitored with
this application is WebSphere MQ (WMQ from now on).

## Features
Zabbix generic discovery will follow all item prototypes, trigger prototypes and graph prototypes with given logic and create copies with correct names for further secondary discovery reasons.

## Requirements
External requirements are:

- [pyzabbix](https://github.com/lukecyca/pyzabbix) python zabbix API implemented
- [requests](http://docs.python-requests.org/en/latest/) "Requests is an Apache2 Licensed HTTP library, written in Python, for human beings."

## Install
Steps to be performed on zabbix server:

 - copy zabbix-generic-discovery.py into /etc/zabbix/externalscripts (or what ever is set in your system as externalscripts location) as zabbix-generic-discovery (without .py extension)
 - create zabbix-generic.discovery.conf as this example (in same directory) :

zabbix-generic-discovery.conf

    [default]
    ; change this to production for example
    server_type = test
    [production]
    zabbix_server = http://production.server.lan/zabbix
    zapi_user = Admin
    zapi_pass = hardcorepassword
    [test]
    zabbix_server = http://test.server.lan/zabbix
    zapi_user = Admin
    zapi_pass = zabbix

Example for WMQ monitoring (reference implementation):

    scp wmq-monitoring.conf root@wmqserver:/etc/zabbix/zabbix-agentd.d/
    ssh root@wmqserver -t visudo # look at example for it in wmq-monitoring.conf
    ssh root@wmqserver mkdir /etc/zabbix/externalscripts
    scp wmq-monitoring-exec root@wmqserver:/etc/zabbix/externalscripts
    ssh root@wmqserver service zabbix-agentd restart

On zabbix frontend create host called "wmqserver" with normal system OS template and after importing wmq-monitoring.template.xml
add just imported "Template WebSphere MQ" template to "wmqserver" server.
After initial discovery new items will be created with special keys that should look something like:
`zabbix-generic-discovery[{HOST.HOST},WMQ_MANAGER_PLACEHOLDER,TESTMQMANAGER]`
Which will be disabled by default, so if you want it to be monitored enable it :-)
After that all discovery rules will be copied and updated to real values (WMQ_MANAGER_PLACEHOLDER -> TESTMQMANAGER) so they should look like:

    wmq.qmgr.discovery
    wmq.qmgr.channel.discovery[TESTMQMANAGER]
    wmq.qmgr.channel.discovery[WMQ_MANAGER_PLACEHOLDER]
    wmq.qmgr.listener.discovery[TESTMQMANAGER]
    wmq.qmgr.listener.discovery[WMQ_MANAGER_PLACEHOLDER]
    wmq.qmgr.queue.discovery[TESTMQMANAGER]
    wmq.qmgr.queue.discovery[WMQ_MANAGER_PLACEHOLDER]

Again enable it and that is it graphs triggers and items should appear soon.

## TODO

Current implementation of example WMQ monitoring is very unoptimized as everything is polled
from zabbix server on each request. Future work will probably use trappers but for
my use case this is sufficient and does not bother system too much (graphs on wmq machine do
not show any significant raise of CPU Utilization).

More explanations how it works is in writing phase.

## License
Apache 2.0

