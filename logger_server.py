import threading
import pickle
import asyncio
import discord
import logging
from aiohttp import ClientSession
from formatter import DiscordColourFormatter

logger = logging.getLogger(__name__)

class LoggerServer(threading.Thread, asyncio.DatagramProtocol):
	def __init__(self, hook_url : str, ip: str = '127.0.0.1', port : int = 1337):
		super().__init__()
		self.hook_url = hook_url
		self.event = threading.Event()
		self.lock = threading.Lock()
		self.exit = False
		self.buffer = ''
		self.addr = (ip, port)
		self.formatter = DiscordColourFormatter()

	async def receiver(self):
		loop = asyncio.get_event_loop()
		self.transport, _ = await loop.create_datagram_endpoint(
			lambda : self,
			local_addr = self.addr)

	def start(self):
		super().start()
		loop = asyncio.new_event_loop()
		task = loop.create_task(self.receiver(), name='Server')

		try:
			loop.run_forever()
		except KeyboardInterrupt:
			self.stop()

		loop.run_until_complete(task)
		loop.close()
		self.join()

	def stop(self):
		self.exit = True
		self.event.set()

	def datagram_received(self, data, addr):
		if data[0]:
			text = data.decode('utf-8')
		else:
			data = pickle.loads(data[4:])
			rec = logging.makeLogRecord(data)
			text = self.formatter.format(rec) + '\n'

		self.lock.acquire()
		self.buffer += text
		self.lock.release()
		self.event.set()

	# Executed in thread
	def run(self):
		asyncio.run(self.sender())
		return 0
	
	# Task sending
	async def sender(self):
		async with ClientSession() as session:
			hook = discord.Webhook.from_url(self.hook_url, session = session)
			while not self.exit:
				# Wait 1 second to combine more logs
				await asyncio.sleep(1)
				self.event.clear()
				self.lock.acquire()
				pos = self.buffer.rfind('\n', 0, 2000)
				if pos < 0:
					self.lock.release()
					self.event.wait()
					continue

				part = self.buffer[:pos]
				self.buffer = self.buffer[pos + 1 :]
				self.lock.release()

				await hook.send(content = '```ansi\n{}```'.format(part),
					username = 'Logger',
					avatar_url = r'https://cdn-icons-png.freepik.com/512/1485/1485257.png')

if __name__ == "__main__":
	from tokens import CHANNEL_HOOK_TEST_LOGGER, LOGGER_PORT
	srv = LoggerServer(CHANNEL_HOOK_TEST_LOGGER, port = LOGGER_PORT)
	srv.start()
