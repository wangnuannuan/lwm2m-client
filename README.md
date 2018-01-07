# lwm2m-client
lwm2m client written in python
###### lwm2m-client is based aiocoap

#### Features provided by the client:
- Functions for connecting and disconnecting from remote servers
- Creation of a COAP server listening for commands issued from the LWM2M Server side linked to handlers defined by the user.
- a dict , to store the current objects and instances along with their resource values and attributes.
- Support for subscriptions from the server


### installation
first,install aiocoap.When the server operates on the client's resources,it needs the request path to call the resources,so I change the code of aiocoap in the file resource.py

	return self._resources[request.opt.uri_path], request.copy(uri_path=request.opt.uri_path) line 253
	return self._resources[request.opt.uri_path], request.copy(uri_path=copy()) the initial code
