import threading
import pickle
import asyncio
import discord
import time
import logging
import sys
import socket
from aiohttp import ClientSession, ClientConnectionError
from formatter import DiscordColourFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LoggerServer(threading.Thread, asyncio.DatagramProtocol):
	FORMAT_STR		= '```ansi\n{}```'
	MAX_LEN			= 2000
	COLLECT_TIMEOUT	= 5

	def __init__(self, hook_url : str, ip: str = '127.0.0.1', port : int = 1337):
		super().__init__(name = 'Uploader')
		self.hook_url = hook_url
		self.event = threading.Event()
		self.lock = threading.Lock()
		self.exit = False
		self.buffer = ''
		self.collect_timeout = 0
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
		logger.debug('Joining thread...')
		self.join()

	def stop(self):
		logger.info('Stopping logger...')
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
		self.collect_timeout = time.monotonic() + self.COLLECT_TIMEOUT
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
			part = ''
			part_add = ''
			while not self.exit:
				max_size = self.MAX_LEN - len(self.FORMAT_STR) - (len(part) + 1 if part else 0)

				self.event.clear()
				self.lock.acquire()
				over_size = len(self.buffer) >= max_size
				timeout = self.collect_timeout - time.monotonic()

				if timeout > 0 and not over_size:
					self.lock.release()
					await asyncio.sleep(timeout)
					continue

				pos = self.buffer.rfind('\n', 0, max_size)
				if not part and not over_size and pos < 0:
					self.lock.release()
					self.event.wait()
					continue

				if pos >= 0:
					part_add = ('\n' if part else '') + self.buffer[:pos]
					self.buffer = self.buffer[pos + 1 : ]
				elif not part:
					# Here pos is -1 and not part, so we have oversize
					part_add = self.buffer[:max_size]
					self.buffer = self.buffer[max_size : ]

				self.lock.release()

				part += part_add
				part_add = ''

				try:
					await hook.send(content = self.FORMAT_STR.format(part))
					part = ''
				except ClientConnectionError as err:
					logger.error('Log upload error: %s', err)
					await asyncio.sleep(10)

if __name__ == "__main__":
	from tokens import CHANNEL_HOOK_TEST_LOGGER, LOGGER_PORT
	logger.addHandler(logging.StreamHandler())

	if len(sys.argv) == 1:
		srv = LoggerServer(CHANNEL_HOOK_TEST_LOGGER, port = LOGGER_PORT)
		srv.start()
	else:
		message = ' '.join(sys.argv[1:])
		logger.info('Sending: %s', message)
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(bytes(message + '\n', "utf-8"), ('127.0.0.1', LOGGER_PORT))

