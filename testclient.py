'''import json
InstanceID=[0,1,2,3,4,5,6,7,8,9]
def oid():
	with open("defs.json") as f:
		def_obj=json.load(f)
	if def_obj.has_key('oid'):
		return [x for x in def_obj['oid'].values()]

def objecturi():
        for oidn in oid():
            for inst in InstanceID:
                yield "</%s/%s>" % (oidn, inst)

def set_objecturi(obj,inst):
        return "</%s/%s>" % (obj, inst)
#
n=0
for path in objecturi():
	print path
	n+=1
# oid_obj=oid()
# print oid_obj
print oid()
print 3331 in oid()
print n
print set_objecturi(3303,0)
import re
object_uri = r'^/\d+/\d+$'   
def parseUri(objectUri):
    if objectUri and re.match(object_uri,objectUri):
    	parse_uri=objectUri.split('/')
        object={'objectType': parse_uri[1],'objectId': parse_uri[2],'objectUri': objectUri}
        return object
    else:
        logger.warn('the objectUri is invalid')
        return False

oid_iid=parseUri('/3303/0')
print oid_iid['objectType']
print oid_iid['objectId']'''

import lwm2mclient
import asyncio
client=lwm2mclient.Client()
client.createResource("/3303/0")
client.createResource("/3304/0")
client.setResource("/3303/0","5700","0")
loop = asyncio.get_event_loop()
asyncio.ensure_future(client.register())
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.close()
    #exit(0)