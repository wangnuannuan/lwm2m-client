import server
import asyncio
from aiohttp import web
import logging
import os
import websockets
import datetime
import random
from threading import Thread
WS_FILE = os.path.join(os.path.dirname(__file__), 'websocket.html')
new_loop=asyncio.new_event_loop()
lwm2mserver=server.Server()


async def hello(websocket,path):
	rec_msg =await websocket.recv()
	print("< {}".format(rec_msg))
	name=rec_msg.split(" ")
	if name[0]=="lwm2m":
		if name[1]=='read':
			endpointname=name[2]
			objmsg=name[3].split("/",3)
			objectType=objmsg[1]
			objectId=objmsg[2]
			resourceId=objmsg[3]
			asyncio.run_coroutine_threadsafe(lwm2mserver.read(endpointname,objectType,objectId,resourceId))
			response=lwm2mserver.get_response()
			await websocket.send(response.payload)
			
	greeting="< {}".format(name)
	await websocket.send(greeting)
	print("> {}".format(greeting))
def index(request):
	with open(WS_FILE, 'rb') as fp:
		return web.Response(body=fp.read(), content_type='text/html')

async def init(loop):
	app=web.Application(loop=loop)
	app.router.add_route('GET', '/', index)
	srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
	logging.info('server started at http://127.0.0.1:9000...')
	return srv
def start_main(loop):
	lwm2mserver.start(loop)
	start_websocket=websockets.serve(hello,'localhost',8756)
	loop.run_until_complete(start_websocket)
	loop.run_until_complete(init(loop))
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		print("Shutting down test server")
		loop.stop()
t=Thread(target=lwm2mserver.start(),args=(new_loop,))
t.start()