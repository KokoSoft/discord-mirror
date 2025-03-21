import discord_self.discord as discord_user
from datetime import datetime, timedelta
import tokens
from channels import *
import asyncio
import forwarder

# Client class
class Alicja(discord_user.Client):
	def __init__(self,
		file_name : str = None,		# Dump entries to specified file
	):
		super().__init__()
		self.file = open(file_name, 'at', encoding='utf-8') if file_name else None
		self.cnt = 0
		self.file_cnt = 0


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
				await self.history_from(channel, 644726298647724053)
				self.file.flush()
			except discord_user.errors.Forbidden:
				pass
		print(f'Done! :) {self.cnt} messages and {self.file_cnt} files')

	# Read message history from a channel
	async def history_from(self, channel, user_id):
		last_id = None
		prev = False
		while prev != last_id:
			prev = last_id
			after = forwarder.Snowflake(last_id) if last_id else datetime(2025, 2, 8, 0, 0, 0)

			async for msg in channel.history(after = after, oldest_first = True, limit = 500):
				last_id = msg.id
				if msg.author.id == user_id:
					self.parse(msg)

			print(f'{channel.id}: History pos',
				discord_user.utils.snowflake_time(last_id).strftime('%Y-%m-%d %H:%M:%S'),
				f'{self.cnt} messages and {self.file_cnt} files')

	def parse(self, msg):
		created_at = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
		entry = f'{msg.channel.name} @ {created_at}: {msg.content}'
		if self.cnt == 0:
			print(entry)

		self.file.write(entry + '\n')

		for f in msg.attachments:
			self.file.write(f'\t{f.filename}\t{f.title}\t{f.url}\n')
			if self.file_cnt == 0:
				print(f'\t{f.filename}\t{f.title}\t{f.url}')
			self.file_cnt += 1

		self.cnt += 1
		pass

alicja = Alicja('alicja.txt')
alicja.run(tokens.L)
