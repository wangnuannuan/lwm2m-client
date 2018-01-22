import asyncio
import time
from threading import Thread
import datetime
import logging
import aiocoap.resource as resource
import aiocoap

class BlockResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.set_content(b"This is the resource's default content. It is padded "\
                b"with numbers to be large enough to trigger blockwise "\
                b"transfer.\n")

    def set_content(self, content):
        self.content = content
        while len(self.content) <= 1024:
            self.content = self.content + b"0123456789\n"

    async def render_get(self, request):
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

class SeparateLargeResource(resource.Resource):

    def get_link_description(self):
        return dict(**super().get_link_description(), title="A large resource")

    async def render_get(self, request):
        await asyncio.sleep(3)

        payload = "Three rings for the elven kings under the sky, seven rings "\
                "for dwarven lords in their halls of stone, nine rings for "\
                "mortal men doomed to die, one ring for the dark lord on his "\
                "dark throne.".encode('ascii')
        return aiocoap.Message(payload=payload)

class TimeResource(resource.ObservableResource):


    def __init__(self):
        super().__init__()

        self.handle = None

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

# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)
def start_loop(loop):
	root = resource.Site()
	root.add_resource(('.well-known', 'core'),resource.WKCResource(root.get_resources_as_linkheader))
	root.add_resource(('time',), TimeResource())
	root.add_resource(('other', 'block'), BlockResource())
	root.add_resource(('other', 'separate'), SeparateLargeResource())
	asyncio.set_event_loop(loop)
	loop.run_until_complete(aiocoap.Context.create_server_context(root, bind=("localhost",5683)))
	loop.run_forever()
 
'''def more_work(x):
    print('More work {}'.format(x))
    time.sleep(x)
    print('Finished more work {}'.format(x))'''

async def main():
	print("self client")
	protocol = await aiocoap.Context.create_client_context()
	request = Message(code=aiocoap.GET, uri='coap://localhost/time')
	try:
		response = await protocol.request(request).response
	except Exception as e:
		print('Failed to fetch resource:')
		print(e)
	else:
		print('Result: %s\n%r'%(response.code, response.payload))

 

new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,))
t.start()

 
#new_loop.call_soon_threadsafe(more_work, 6)
#new_loop.call_soon_threadsafe(more_work, 3)
asyncio.run_coroutine_threadsafe(main(),new_loop)