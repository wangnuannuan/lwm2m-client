from aiocoap import *
import aiocoap.resource as resource
import asyncio
import re
object_uri = r'^/\d+/\d+$'   
import logging   
import json
from lwm2mclient import definitions
logging.basicConfig(level=logging.DEBUG,format='%(levelname)s %(message)s')    
logger = logging.getLogger('lwm2mclient')  
client_resource={}
class ObjectRouter(object):
    InstanceID=[0,1,2,3,4,5,6,7,8,9]
    def __init__(self): #,def_object="defs.json"):
        # with open(def_object) as f:
        self.definition= definitions.device#json.load(f)

    def objects_oid(self):
        if "oid" in self.definition:
            return [x for x in self.definition['oid'].values()]
    def objects_uniqueRid(self):
        if "uniqueRid" in self.definition:
            return [x for x in self.definition['uniqueRid'].values()]
    def objecturi(self):
        for oid in self.objects_oid():
            for inst in self.InstanceID:
                yield "</%s/%s>" % (obj, inst)
    def oid_iid_rid(self):
        for oid in self.objects_oid():
            for inst in self.InstanceID:
                for rid in self.objects_uniqueRid():
                    yield (str(oid), str(inst), str(rid))
    def is_oid(self,oid):
        return int(oid) in self.objects_oid()
    def is_iid(self,iid):
        return int(iid) in self.InstanceID
    def set_objecturi(self,obj,inst):
        return "</%s/%s>" % (obj, inst)
    def is_rid(self,rid):
        return int(rid) in self.objects_uniqueRid()

class ObjRegistry(object):
    registry_client={} 
    attributesRegistry = {}
    '''the path like :"/3303/0" '''
    def parseUri(self,objectUri):
        if objectUri and re.match(object_uri,objectUri):
            parse_uri=objectUri.split('/')
            object={'objectType': parse_uri[1],'objectId': parse_uri[2],'objectUri': objectUri}
            return object
        else:
            logger.warn('the objectUri is invalid')
            return False
    def getObject(self,objectUri):
        if self.parseUri(objectUri):
            Objectvalue=self.registry_client.get(objectUri)
            if Objectvalue or Objectvalue=={}:
                return Objectvalue
            else:
                logger.warn('can not find the object')
                return False

    def create(self,objectUri):
        if self.parseUri(objectUri):
            self.registry_client[objectUri]={}
    def remove(self,objectUri):
        if self.parseUri(objectUri):
            Objectvalue=self.registry_client.get(objectUri)
            if Objectvalue:
                removedObj=self.registry_client.pop(objectUri)
                logger.debug('remove the object: '+objectUri)
                return removedObj
            else:
                logger.error('can not find the object')
    def list(self):
        print(self.registry_client)

    def set(self,objectUri, resourceId, resourceValue):
        if self.parseUri(objectUri):
            if self.getObject(objectUri):
                self.registry_client[objectUri]={resourceId: resourceValue}
            else:
                self.create(objectUri)
                self.registry_client[objectUri]={resourceId:resourceValue}

    def unset(self,objectUri, resourceId):
        if self.parseUri(objectUri):
            if self.getObject(objectUri):
                if self.registry_client[objectUri].get(resourceId):
                    self.registry_client[objectUri].pop(resourceId)
                else:
                    logger.warn('the resourceId not exist')
    def resetRegistry(self):
        self.registry_client={}
        self.attributesRegistry = {}
        logger.debug('Removes all information an handlers from the registry')

    def setAttributes(self,uri, attributes):
        try:
            self.attributesRegistry[uri] = attributes
        except:
            logger.error('can not set Attributes ')
    def getAttributes(self,uri):
        try:
            if attributesRegistry.get(uri):
                return self.attributesRegistry[uri]
            else:
                logger.warn('the object type, instance or resource not exist')
        except:
            logger.error('can not get the Attributes ' )

class RequestHandler(resource.ObservableResource):

    def handle_read(self,path):
        # print("read_path"+str(path))
        value=client_resource[path[0]][path[1]][path[2]]
        value=value.encode()
        return Message(payload=value)


    def handle_write(self,path,payload,content_format):
        client_resource[path[0]][path[1]][path[2]]= payload.decode()
        print("set the value of "+str(path)+" to "+str(payload))
        return Message(code=CONTENT,payload=b"")
        # return self.decoder.decode(path, payload, content_format)
        # print("path "+str(path)+" payload "+str(payload)+" content_format "+str(content_format))
    def handle_observe(self,request):
        path =request.opt.uri_path
        path_length=len(path)
        if path_length == 1:
            obs = "observe_%s" % path[0]
        elif path_length == 2:
            obs = "observe_%s_%s" % (path[0], path[1])
        elif path_length == 3:
            obs = "observe_%s_%s_%s" % (path[0], path[1], path[2])
        else:
            return Message(code=Code.BAD_REQUEST)
        def _notifier():
            self.update_state() # 
        return Message(code=METHOD_NOT_ALLOWED)
    def handle_exec(self,request):
        path = request.opt.uri_path
        print("handle_exec "+path)
        if len(path) !=3:
            return Message(code=BAD_REQUEST)
        return Message(code=CHANGED)
    async def render_get(self,request):
        if request.opt.observe is not None:
            logger.debug("observe on %s" % "/".join(request.opt.uri_path))
            return self.handle_observe(request)
        else:
            logger.debug("read on %s" % "/".join(request.opt.uri_path))
            return self.handle_read(request.opt.uri_path)
    async def render_put(self,request):
        logger.debug("write on %s" % "/".join(request.opt.uri_path))
        return self.handle_write(request.opt.uri_path, request.payload, request.opt.content_format)
    async def render_post(self,request):
        logger.debug("execute on %s" % "/".join(request.opt.uri_path))
        return self.handle_exec(request)

class Client(ObjRegistry,resource.Site):
    #host='localhost'
    port=5683
    code='GET'
    payload=[]
    endpointName="lwm2mc"
    binding_mode = "UQ"
    lifetime=86400
    version='1.0'
    observers={}
    content=None
    rd_resource = None
    def __init__(self,host='localhost',port=5683,model=ObjectRouter()):
        super(Client,self).__init__()
        self.host=host
        self.port=port
        self.model=model
        self.request_handler=RequestHandler()

    def createResource(self,objectUri):
        logger.debug("create resource")
        self.create(objectUri) # "/3303/0"
        oid_iid=self.parseUri(objectUri)
        if oid_iid:
            if self.model.is_oid(oid_iid['objectType']):
                if self.model.is_iid(oid_iid['objectId']):
                    client_resource[oid_iid['objectType']]={oid_iid['objectId']:{}}
                    self.add_resource(self.model.set_objecturi(oid_iid['objectType'],oid_iid['objectId']),
                        self.request_handler)
                    self.payload.append(self.model.set_objecturi(oid_iid['objectType'],oid_iid['objectId']))
                    print(self.model.set_objecturi(oid_iid['objectType'],oid_iid['objectId']))
        try:
            self.list()
        except:
            logger.error("list error")

    def setResource(self,objectUri, resourceId, resourceValue):
        self.set(objectUri, resourceId, resourceValue)
        oid_iid=self.parseUri(objectUri)
        if oid_iid:
            if self.model.is_oid(oid_iid['objectType']):
                if self.model.is_iid(oid_iid['objectId']):
                    if self.model.is_rid(resourceId):
                        client_resource[oid_iid['objectType']][oid_iid['objectId']]={resourceId:resourceValue}
                        self.add_resource((str(oid_iid['objectType']),str(oid_iid['objectId']),str(resourceId)),
                            self.request_handler)
        try:
            self.list()
        except:
            logger.error("list error")

    async def register(self):
        self.context = await Context.create_server_context(self,bind=("::", 0))#bind=("localhost", 0))
        request = Message(code=POST, payload=','.join(self.payload).encode())
        request.opt.uri_host=self.host
        request.opt.uri_port=self.port
        request.opt.uri_path=("rd",)
        request.opt.uri_query = ("ep=%s" % self.endpointName, "b=%s" % self.binding_mode, "lt=%d" % self.lifetime)
        response = await self.context.request(request).response
        print('Result: %s\n%r'%(response.code, response.payload))
        if response.code != Code.CREATED:
            raise BaseException("unexpected code received: %s. Unable to register!" % response.code)
        self.rd_resource = response.opt.location_path[0]# .decode()
        print("client registered at location %s" % self.rd_resource)
        await asyncio.sleep(self.lifetime - 1)
        asyncio.ensure_future(self.updateRegistration())
        

    async def unregister(self,endpointname):
        self.context = await Context.create_server_context(self, bind=("::", 0))
        request.opt.uri_host=self.host
        request.opt.uri_port=self.port
        request.opt.uri_path=("rd",)
        request.opt.uri_query = ("ep=%s" % endpointname, "b=%s" % self.binding_mode, "lt=%d" % self.lifetime)
        response = await self.context.request(request).response
        print('Result: %s\n%r'%(response.code, response.payload))


    async def updateRegistration(self):
        logger.debug("update_register()")
        request = Message(code=POST)
        request.opt.uri_host=self.host
        request.opt.uri_port=self.port
        request.opt.uri_path=("rd", self.rd_resource)
        response = await self.context.request(request).response
        if response.code != Code.CHANGED:
            logger.warn("failed to update registration, code {}, falling back to registration".format(response.code))
            asyncio.ensure_future(self.register())
        else:
            logger.info("updated registration for %s" % self.rd_resource)
            # yield to next update - 1 sec
            await asyncio.sleep(self.lifetime - 1)
            asyncio.ensure_future(self.updateRegistration())

    async def cancelObserver(self,objUri,resourceId):
        pass

    async def cancellAllObservers():
        pass
    async def listObservers():
        pass


