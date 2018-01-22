import asyncio 
import aiocoap

import logging
import time
import os
import re
import hashlib
import aiocoap.resource as resource
logging.basicConfig(level=logging.DEBUG,format='%(levelname)s %(message)s')    
logger = logging.getLogger('lwm2mserver')  

class Hasher(object):
    def __init__(self, seed):
        self.seed = seed

    def hash_for(self, string):
        assert string is not None
        h = hashlib.new("sha1")
        h.update(string.encode())
        h.update(self.seed)
        return h.hexdigest()

class Registry_device():
    def getByName(self,registrys,devicename):
        for k in registrys:
            if registrys[k]["endpoint"]==devicename:
                return registrys[k]

    def unregister(self,registrys,id):
        if registrys.get(id):
            del registrys[id]
        else:
            logger.error("not found the id ")
    def register(self,registrys,idnum,device):
        registrys[idCounter]=device
        registrys[idCounter]['id']=idCounter

    def clean(self,registrys):
        registrys={}
    
    def getObject(self,registrys,id):
        if registrys.get(id):
            return registrys[id]
        else:
            return None


    def update(self,registrys,id,obj):
        if registrys.get(id):
            registrys[id]=obj
        else:
            logger.error("not found the id")
    def list(self,registrys):
        print(registrys)
    def stopLifetimeCheck(self):
        pass
    def checkLifetime(self):
        pass

class WithAsyncloop():
    def __init__(self):
        self.loop=asyncio.get_event_loop()

class WithClient(WithAsyncloop):
    def __init__(self):
        super(WithClient,self).__init__()
        self.client=self.loop.run_until_complete(aiocoap.Context.create_client_context())

    def close(self):
        self.loop.run_until_complete(self.client.shutdown())

    def fetch_response(self,request,exchange_monitor_factory=lambda x:None):
        return self.loop.run_until_complete(self.client.request(request, exchange_monitor_factory=exchange_monitor_factory).response)

class DeviceManagement(WithClient,Registry_device):
    def __init__(self):
        super(DeviceManagement,self).__init__()
    def read(self,registrys,deviceId, objectType, objectId, resourceId):
        obj=self.getByName(registrys,deviceId)
        print(obj)
        request=aiocoap.Message(code=aiocoap.GET)
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        request.opt.uri_path=(objectType, objectId, resourceId)
        return request
    def write(self,registrys,deviceId, objectType, objectId, resourceId, value):
        obj=self.getByName(registrys,deviceId)
        request=aiocoap.Message(code=aiocoap.PUT)
        request.payload=value
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        request.opt.uri_path=(objectType, objectId, resourceId)
        return request

    def execute(self,registrys,deviceId, objectType, objectId, resourceId, value):
        obj=self.getByName(registrys,deviceId)
        request=aiocoap.Message(code=aiocoap.POST)
        request.payload=value
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        request.opt.uri_path=(objectType, objectId, resourceId)
        return request
    def writeAttributes(deviceId, objectType, objectId, resourceId, attributes):
            pass
    def discover(self,registrys,deviceId, objectType, objectId, resourceId):
        obj=self.getByName(registrys,deviceId)
        logger.debug('Executing a resource discover operation on resource')

        request=aiocoap.Message(code=aiocoap.GET)
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        print(obj["objects"])
        request.opt.accept=aiocoap.numbers.media_types_rev['application/link-format']
        if obj["objects"].get(objectType):
            if obj["objects"][objectType].get(objectId):
                if obj["objects"][objectType][objectId]==resourceId:
                    request.opt.uri_path=(objectType,objectId,resourceId)
                else:
                    request.opt.uri_path=(objectType,objectId)
            else:
                request.opt.uri_path=(objectType,) 
        return request
    def create(self,registrys,deviceId, objectType, objectId):
        obj=self.getByName(registrys,deviceId)
        logger.debug('Creating a new instance of object type [%s] in the device [%d] with instance id [%s]',objectType, deviceId, objectId)
        request=aiocoap.Message(code=aiocoap.POST)
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        request.opt.uri_path=(deviceId, objectType)
        return request
    def remove(self,deviceId, objectType, objectId):
        pass
    def observe_parseId():
        pass
    def observe(self,registrys,deviceId, objectType, objectId,resourceId):
        obj=self.getByName(registrys,deviceId)
        serveraddress = "::1"
        servernetloc = "[%s]"%serveraddress
        logger.debug('Observing value from resource /%s/%s/%s in device [%d]',objectType, objectId, resourceId, deviceId)
        request = aiocoap.Message(code=aiocoap.GET)
        request.unresolved_remote = servernetloc
        request.remote=obj["address"]
        request.opt.uri_host=obj["host"]
        request.opt.uri_port=obj["port"]
        request.opt.uri_path = (objectType,objectId,resourceId)
        request.opt.observe = 1
        return request

    def list_observe(self):
    	print(subscriptions)
    def clean_observe(self):
    	subscriptions={}
    def cancel_observe(self,deviceId, objectType, objectId, resourceId):
    	pass

class Server(DeviceManagement,resource.ObservableResource):
    host='localhost'
    port=5683
    lifetime=86400
    version='1.0.0'
    log_level="DEBUG"
    ENDPOINT = "ep"
    LIFETIME = "lt"
    BINDING_MODE = "b"
    SMS = "sms"
    LWM2M_VERSION = "lwm2m"
    DEFAULT_VERSION = "1.0"
    DEFAULT_LIFETIME = 86400
    CLEANER_PERIOD_SECONDS = 10
    site=aiocoap.resource.Site()
    registry={}
    idCounter=1
    subscriptions = {}

    def __init__(self):
        super(Server,self).__init__()
        logger.debug("creating server instance")
        self.hasher = Hasher(os.urandom(30))
        self.site = resource.Site()
        self.site.add_resource((self.get_path(),), self)
        self.handle=None

    def notify(self):
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.handle = self.reschedule()
        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None

    async def render_get(self, request):
        payload = datetime.datetime.now().\
                strftime("%Y-%m-%d %H:%M").encode('ascii')
        return aiocoap.Message(payload=payload)    


    @staticmethod
    def get_path():
        return "rd"

    def get_device_location(self,location):
        for k in self.registry:
            if self.registry[k]['location']==location:
                return self.registry[k]
    async def render_post(self, request):
        print(request.opt.uri_host)
        print(request.opt.uri_port)
        address=request.remote
        opts = dict(x.split("=") for x in request.opt.uri_query)
        logger.debug("POST called with options %s" % opts)

        if self.ENDPOINT not in opts:
            return self.bad_request(b"endpoint name is required")

        client = dict()
        client["address"]=address
        client["host"]=self.host
        client["port"]=self.port
        client["endpoint"] = opts[self.ENDPOINT]
        client["lifetime"] = self._get_lifetime(opts, self.DEFAULT_LIFETIME)

        client["lwm2m_version"] = opts[self.LWM2M_VERSION] if self.LWM2M_VERSION in opts else self.DEFAULT_VERSION
        client["sms"] = opts[self.SMS] if self.SMS in opts else None
        client["binding_mode"] = self.get_binding_mode(
            opts[self.BINDING_MODE]) if self.BINDING_MODE in opts else "U"
        payload = request.payload.decode()
        if payload == "":
            return self.bad_request(b"payload must contain object links")

        client["objects"] = self.get_object_links(request.payload.decode())
        client["time"] = asyncio.get_event_loop().time()
        location=self.hasher.hash_for(opts[Server.ENDPOINT])

        client['location']=location
        self.registry[self.idCounter]=client
        registrys=self.registry



        self.idCounter +=1

        self.site.add_resource((self.get_path(), location), self)
        response = aiocoap.Message(code=aiocoap.CREATED)
        return response

    def _get_lifetime(self, opts, default_lifetime):
        if self.LIFETIME in opts:
            try:
                lifetime = int(opts[Server.LIFETIME])
            except ValueError:
                return Server.bad_request(b"non-numeric lifetime value")

            if lifetime <= 0:
                return Server.bad_request(b"lifetime value out of range")
            else:
                return lifetime
        else:
            return default_lifetime

    def _remove_client(self, location):
        self.site.remove_resource((self.get_path(), location))

    @staticmethod
    def get_binding_mode(bmode):
        modes = ["U", "UQ", "S", "SQ", "US", "UQS"]
        return bmode if bmode in modes else "U"

    @staticmethod
    def get_object_links(payload):
        objs = dict()
        for link in payload.split(","):
            m = re.match("^<(/(\d+))(/(\d+))*>.*$", link)
            if m.group(4) is not None:
                obj_id = str(m.group(2))
                instance_id = str(m.group(4))
                if obj_id in objs:
                    objs[obj_id][instance_id] = instance_id
                else:
                    objs[obj_id] = {instance_id: instance_id}
            else:
                obj_id = str(m.group(2))
                if obj_id in objs:
                    objs[obj_id]["0"] = "0"
                else:
                    objs[obj_id] = {"0": "0"}

        return objs

    @staticmethod
    def bad_request(payload=None):
        response = aiocoap.Message(code=aiocoap.BAD_REQUEST)
        if payload is not None:
            response.payload = payload
        return response

    @asyncio.coroutine
    def render_put(self, request):
        location = request.opt.uri_path[-1]
        logger.debug("PUT called for location %s" % location)
        opts = dict(x.split("=") for x in request.opt.uri_query)
        client = self.get_device_location(location)# self.client_persistence.get_client_for_location(location)
        client["time"] = asyncio.get_event_loop().time()
        client["lifetime"] = self._get_lifetime(opts, client["lifetime"])
        client["binding_mode"] = self.get_binding_mode(
            opts[self.BINDING_MODE]) if self.BINDING_MODE in opts else client["binding_mode"]
        client["sms"] = opts[self.SMS] if self.SMS in opts else client["sms"]
        payload = request.payload.decode()
        if payload != "":
            client["objects"] = self.get_object_links(payload)
        registrys=self.registry

        response = aiocoap.Message(code=aiocoap.CHANGED)
        return response

    @asyncio.coroutine
    def render_delete(self, request):
        location = request.opt.uri_path[-1]
        logger.debug("DELETE called for location %s" % location)
        self._remove_client(location)
        response = aiocoap.Message(code=aiocoap.DELETED)
        return response

    def notify(self):
        self.updated_state()
        self.reschedule()

    def cleaner(self):
        logger.debug("running periodic cleaner")
        to_delete = list()
        for k in self.registry:
            time = asyncio.get_event_loop().time()
            if time - self.registry[k]["time"] > self.registry[k]["lifetime"]:
                to_delete.append(self.registry[k]["location"])
        for location in to_delete:
            logger.debug("removing dead client (location %s)" % location)
            self._remove_client(location)
        # reschedule the cleaner
        asyncio.get_event_loop().call_later(self.CLEANER_PERIOD_SECONDS, self.cleaner)
    async def start(self):
        self.protocol= await aiocoap.Context.create_server_context(self.site,bind=(self.host, self.port))
        self.protocol1=await aiocoap.Context.create_client_context()
        # asyncio.ensure_future(self.protocol)
        # self.server = self.loop.run_until_complete(self.protocol)
    def stop(self):
        self.loop.run_until_complete(asyncio.sleep(CLEANUPTIME))
        self.loop.run_until_complete(self.server.shutdown())







