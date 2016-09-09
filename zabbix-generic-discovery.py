#!/usr/bin/env python
"""
 Copyright 2014 Boris Manojlovic boris@steki.net

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from pyzabbix import ZabbixAPI, ZabbixAPIException
from pprint import pprint
import sys # arguments parsing...
try:
    import ConfigParser as configparser  # Py2
except ImportError:
    import configparser
from datetime import datetime

if len(sys.argv) < 4:
    print ("\n"
           "    This program is supposed to receive three arguments\n"
           "    1) Hostname this discovery script is called from\n"
           "    2) What is name of variable that should be replaced in discovery\n"
           "    3) Replacement value\n"
           "  "
    )
    sys.exit()

print ("ZGD:%s:START" % str(datetime.now()) )

# cat zabbix-generic-discovery.conf
# [default]
# ; change this to production for example
# server_type = test
# [production]
# zabbix_server = http://127.0.0.1/zabbix
# zapi_user = Admin
# zapi_pass = zabbix
# [test]
# zabbix_server = http://localhost/zabbix
# zapi_user = Admin
# zapi_pass = zabbix
config = configparser.RawConfigParser()
config.read(sys.path[0]+'/zabbix-generic-discovery.conf')
s = config.get('default','server_type')

zapi = ZabbixAPI(config.get(s,'zabbix_server'))
zapi.login(config.get(s,'zapi_user'), config.get(s,'zapi_pass'))


HOSTNAME = sys.argv[1]
PLACEHOLDER = sys.argv[2]
REPLACEMENT = sys.argv[3]

hostid = zapi.host.get(filter={"host": HOSTNAME})[0]['hostid']
if not hostid:
    raise NoHostFound

def graph_item_get(hostid, itemid, PLACEHOLDER,REPLACEMENT):
    """
    Return itemid of item with corrected key_ 
    """
    origitemproto = (zapi.itemprototype.get(hostids=hostid, itemids=itemid, output="extend",selectApplications={}))[0]
    origitemproto['key_'] = origitemproto['key_'].replace( PLACEHOLDER, REPLACEMENT)
    fixed_itemid = zapi.itemprototype.get(hostids=hostid, search = {'key_':origitemproto['key_'] })
    if len(fixed_itemid) > 0:
        print ("found itemprototype with key = %s" % origitemproto["key_"])
    return fixed_itemid[0]

for drule in zapi.discoveryrule.get(hostids=hostid, selectItems={}, selectGraphs={},  selectTriggers={},
                                    selectHostPrototypes={}, search={"key_": PLACEHOLDER}):
    """ Create discovery rule based on template """
    drule_c = zapi.discoveryrule.get(itemids=drule['itemid'], output="extend")[0]
    drule_c["key_"] = drule_c["key_"].replace( PLACEHOLDER, REPLACEMENT)
    drule_c["name"] = drule_c["name"].replace( PLACEHOLDER, REPLACEMENT)
    del drule_c['itemid']
    del drule_c['templateid']
    del drule_c['state']
    drule_created = zapi.discoveryrule.get(hostids=hostid, search={"key_":drule_c["key_"]})
    if len(drule_created) == 0:
        print ("created discovery rule with key = %s" % drule_c["key_"])
        drule_itemid = zapi.discoveryrule.create(drule_c)['itemids'][0]
    else:
        drule_itemid = drule_created[0]['itemid']

    """ Create Items based on templates """
    for itemprotoid in drule['items']:
        itemproto = (zapi.itemprototype.get(hostids=hostid, itemids=itemprotoid, output="extend",selectApplications={}))[0]
        itemproto['key_'] = itemproto['key_'].replace( PLACEHOLDER, REPLACEMENT)
        itemproto['name'] = itemproto['name'].replace( PLACEHOLDER, REPLACEMENT)
        del itemproto['itemid']
        del itemproto['templateid']
        del itemproto['state']
        itemproto['applications'] = itemproto['applications'][0]
        itemproto[u'ruleid'] = drule_itemid
        if len(zapi.itemprototype.get(hostids=hostid, search = {'key_':itemproto['key_']})) == 0:
            print ("created itemprototype with key = %s" % itemproto["key_"])
            zapi.itemprototype.create(itemproto)

    """ Create triggers on created prototype items """
    for triggerprotoid in drule['triggers']:
        triggerproto = (zapi.triggerprototype.get(triggerids=triggerprotoid, output="extend",expandExpression="true"))[0]
        del triggerproto['templateid']
        del triggerproto['triggerid']
        triggerproto['description'] = triggerproto['description'].replace( PLACEHOLDER, REPLACEMENT)
        triggerproto['expression'] = triggerproto['expression'].replace( PLACEHOLDER, REPLACEMENT)
        try:
            zapi.triggerprototype.create(triggerproto)
        except ZabbixAPIException as e:
            if e.args[1] != -32602:
                raise
        else:
            print ("created triggerproto with expression = %s" % triggerproto["expression"])

    """ Create graphs on created prototype items """
    for graphprotoid in drule['graphs']:
        graphprotoitems = (zapi.graphitem.get(graphids=graphprotoid, selectItems={}, selectGraphItems={}, output="extend"))
        gitems = []
        for gitem in graphprotoitems:
            gitem['itemid'] = graph_item_get(hostid, gitem['itemid'], PLACEHOLDER, REPLACEMENT)['itemid']
            del gitem['graphid']
            del gitem['gitemid']
            gitems.append(gitem)

        graphproto = zapi.graphprototype.get(hostids=hostid, graphids=graphprotoid, output="extend")[0]
        graphproto['name'] = graphproto['name'].replace( PLACEHOLDER, REPLACEMENT)
        del graphproto['graphid']
        del graphproto['templateid']
        graphproto['gitems'] = gitems
        if len(zapi.graphprototype.get(hostids=hostid, search={'name':graphproto['name']})) == 0:
            print ("created graphprototype with name = %s" % graphproto["name"])
            zapi.graphprototype.create(graphproto)

    """ Create hosts on created prototype items """
    """ TODO """

print ("ZGD:%s:STOP" % str(datetime.now()) )
