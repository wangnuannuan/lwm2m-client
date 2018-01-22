import server
import asyncio
from aiohttp import web
import logging
import os
import websockets
import datetime
import random
import aiocoap
LwM2M_FILE = os.path.join(os.path.dirname(__file__), 'template/websocket.html')
CoAP_FILE=os.path.join(os.path.dirname(__file__),"template/coap.html")
MQTT_FILE=os.path.join(os.path.dirname(__file__),"template/mqtt.html")

lwm2mserver=server.Server()

asyncio.ensure_future(lwm2mserver.start())
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
			protocol = lwm2mserver.protocol# await aiocoap.Context.create_client_context()
			request=lwm2mserver.read(lwm2mserver.registry,endpointname,objectType,objectId,resourceId)
			try:
				response = await protocol.request(request).response
			except Exception as e:
				await websocket.send('Failed to fetch resource:')
				print(e)
			else:
				print(response.payload)
				await websocket.send("the value of "+name[3]+" in "+endpointname+": "+response.payload.decode())
		elif name[1]=="write":
			endpointname=name[2]
			objmsg=name[3].split('/',3)
			objectType=objmsg[1]
			objectId=objmsg[2]
			resourceId=objmsg[3]
			value=name[4].encode()
			protocol=lwm2mserver.protocol
			request=lwm2mserver.write(lwm2mserver.registry,endpointname,objectType,objectId,resourceId,value)
			try:
				response = await protocol.request(request).response
			except Exception as e:
				await websocket.send('Failed to fetch resource:')
				print(e)
			else:
				print(response.payload)
				await websocket.send("set the value of "+name[3]+" in "+endpointname+": "+name[4])
		elif name[1]=="observe":
			endpointname=name[2]
			objmsg=name[3].split("/",3)
			objectType=objmsg[1]
			objectId=objmsg[2]
			resourceId=objmsg[3]
			protocol = lwm2mserver.protocol# await aiocoap.Context.create_client_context()
			request=lwm2mserver.read(lwm2mserver.registry,endpointname,objectType,objectId,resourceId)
			try:
				pr=protocol.request(request)
				response= await pr.response
			except Exception as e:
				await websocket.send('Failed to fetch resource:')
				print(e)
			else:
				await websocket.send("first response: "+response.payload.decode())

		elif name[1]=="execute":
			endpointname=name[2]
			objmsg=name[3].split('/',3)
			objectType=objmsg[1]
			objectId=objmsg[2]
			resourceId=objmsg[3]
			value=name[4].encode()
			protocol=lwm2mserver.protocol
			request=lwm2mserver.execute(lwm2mserver.registry,endpointname,objectType,objectId,resourceId,value)
			try:
				response = await protocol.request(request).response
			except Exception as e:
				await websocket.send('Failed to fetch resource:')
				print(e)
			else:
				print(response.payload)
				await websocket.send("execute the value of "+name[3]+" in "+endpointname+": "+name[4])
		elif name[1]=="discover":
			endpointname=name[2]
			objmsg=name[3].split("/",3)
			objectType=objmsg[1]
			objectId=objmsg[2]
			resourceId=objmsg[3]
			protocol = lwm2mserver.protocol
			request=lwm2mserver.discover(lwm2mserver.registry,endpointname,objectType,objectId,resourceId)
			try:
				response = await protocol.request(request).response
			except Exception as e:
				await websocket.send('Failed to fetch resource:')
				print(e)
			else:
				print(response.payload)
				await websocket.send("discover from "+name[3]+" in "+endpointname+": "+response.payload.decode())
		else:
			await websocket.send("error request")
	# elif name[0]=="coap":



def lwm2m_index(request):
	with open(LwM2M_FILE, 'rb') as fp:
		return web.Response(body=fp.read(), content_type='text/html')
def coap_index(request):
	with open(CoAP_FILE, 'rb') as fp:
		return web.Response(body=fp.read(), content_type='text/html')
def mqtt_index(request):
	with open(MQTT_FILE, 'rb') as fp:
		return web.Response(body=fp.read(), content_type='text/html')


async def init(loop):
	app=web.Application(loop=loop)
	app.router.add_route('GET', '/lwm2m', lwm2m_index)
	app.router.add_route('GET','/',coap_index)
	app.router.add_route('GET','/mqtt',mqtt_index)
	srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
	logging.info('server started at http://127.0.0.1:9000...')
	return srv

start_websocket=websockets.serve(hello,'localhost',8756)
lwm2mserver.loop.run_until_complete(start_websocket)
lwm2mserver.loop.run_until_complete(init(lwm2mserver.loop))
try:
	lwm2mserver.loop.run_forever()

except KeyboardInterrupt:
	print("Shutting down test server")
	s.stop()
else:
	if lwm2mserver.loop.is_closed():
		lwm2mserver.loop.run_forever()