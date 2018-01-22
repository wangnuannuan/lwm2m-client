import asyncio

async def slow_operation(future):
    await asyncio.sleep(1)
    future.set_result('Future is done!')

def got_result(future):
    print(future.result())
    loop.stop()

loop = asyncio.get_event_loop()
future = asyncio.Future()
asyncio.ensure_future(slow_operation(future))
future.add_done_callback(got_result)
try:
    loop.run_forever()
finally:
    loop.close()
'''******************************************************'''
import asyncio

async def slow_operation(future):
    await asyncio.sleep(1)
    future.set_result('Future is done!')

loop = asyncio.get_event_loop()
future = asyncio.Future()
asyncio.ensure_future(slow_operation(future))
loop.run_until_complete(future)
print(future.result())
loop.close()
'''********************************************************'''
import asyncio

async def factorial(name, number):
    f = 1
    for i in range(2, number+1):
        print("Task %s: Compute factorial(%s)..." % (name, i))
        await asyncio.sleep(1)
        f *= i
    print("Task %s: factorial(%s) = %s" % (name, number, f))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
    factorial("A", 2),
    factorial("B", 3),
    factorial("C", 4),
))
loop.close()
'''*********************************************************'''
AbstractEventLoop.run_forever()
AbstractEventLoop.run_until_complete(future)
AbstractEventLoop.is_running()
AbstractEventLoop.stop()
AbstractEventLoop.is_closed()
AbstractEventLoop.close()
coroutine AbstractEventLoop.shutdown_asyncgens()
try:
    loop.run_forever()
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
'''*********************************************************'''
AbstractEventLoop.call_soon(callback, *args)
AbstractEventLoop.call_soon_threadsafe(callback, *args)

AbstractEventLoop.call_later(delay, callback, *args)
AbstractEventLoop.call_at(when, callback, *args)
AbstractEventLoop.time()