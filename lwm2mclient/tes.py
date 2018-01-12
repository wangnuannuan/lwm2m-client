
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
