import discord_self.discord as discord_user
from datetime import datetime, timedelta
import tokens
from channels import *
import asyncio
import forwarder

# Client class
class Wonsik(discord_user.Client):
	def __init__(self,
		file_name : str = None,		# Dump entries to specified file
	):
		super().__init__()
		self.file = open(file_name, 'at', encoding='utf-8') if file_name else None
		self.cnt = 0

	def __del__(self):
		if self.file:
			self.file.close()

	# On Client ready
	async def on_ready(self):
		self.on_ready_task = asyncio.current_task()
		print('Logged on as', self.user)

		try:
			# Set user presence
			await self.change_presence(status = discord_user.Status.invisible)

			await self.history()
		except GeneratorExit:
			pass

	async def history(self):
		gej = self.get_guild(1079122293281787974)
		for channel in gej.channels:
			if channel.type is not discord_user.ChannelType.text:
				continue

			print(f"Parsing {str(channel.type):12} {channel.id} {channel.name}")
			try:
				await self.history_from(channel, 1076532240877621249)
				self.file.flush()
			except discord_user.errors.Forbidden:
				pass
		print(f'Done! :) {self.cnt} messages')

	# Read message history from a channel
	async def history_from(self, channel, user_id):
		last_id = None
		prev = False
		while prev != last_id:
			prev = last_id
			after = forwarder.Snowflake(last_id) if last_id else datetime(2025, 2, 31, 0, 0, 0)

			async for msg in channel.history(after = after, oldest_first = True, limit = 500):
				last_id = msg.id
				if msg.author.id == user_id:
					self.parse(msg)

			print(f'{channel.id}: History pos',
				discord_user.utils.snowflake_time(last_id).strftime('%Y-%m-%d %H:%M:%S'),
				f'{self.cnt} messages')

	def parse(self, msg):
		entry = f'{msg.id} {msg.channel.id}'
		if self.cnt == 0:
			print(entry)

		self.file.write(entry + '\n')

		self.cnt += 1
		pass

alicja = Wonsik('wonsik.txt')
alicja.run(tokens.K)
