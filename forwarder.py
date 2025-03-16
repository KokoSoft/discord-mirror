from ctypes import Union
from typing import Sequence
from collections.abc import Callable
import discord as discord_bot
import discord_self.discord as discord_user
import asyncio
import json
from hashlib import md5
from functools import cmp_to_key
from datetime import datetime
import inspect

#debug only
import sys

class Snowflake:
	def __init__(self, id):
		self.id = id

def print_channel_list(con):
	def channel_sort(a, b):
		a_cat = None if a.category is None else a.category.id
		a_pos = a.position
		b_cat = None if b.category is None else b.category.id
		b_pos = b.position

		# same category or both are None
		if a_cat == b_cat:
			return a_pos - b_pos

		if a_cat is None or b_cat is None:
			if a_cat is None:
				d = a_pos - cat_pos[b_cat]
			else:
				d = cat_pos[a_cat] - b_pos

			# Category with channel in this category
			if d == 0:
				return -1 if a_cat is None else 1

			return d

		return cat_pos[a_cat] - cat_pos[b_cat]

	for guild in con.guilds:
		print(guild.name)
		channels = list(guild.channels)
		cat_pos = { ch.id:ch.position for ch in channels if ch.category is None }
		channels.sort(key=cmp_to_key(channel_sort))

		for ch in channels:
			print(f"{str(ch.type):12} {ch.id} {ch.name}")

def is_async(obj):
	return asyncio.iscoroutinefunction(obj) or \
		(hasattr(obj, '__call__') and asyncio.iscoroutinefunction(obj.__call__))

# Use this class to copy received message.
# The original message is stored in a discord.py cache
class ParsedMessage:
	def __init__(self, message):
		self.content = message.content
		self.embeds = [emb for emb in message.embeds if emb.type != 'gifv' ]
		self.attachments = list(message.attachments)

# Use this class to copy received message for a WebHook.
# The original message is stored in a discord.py cache
class ParsedWebHookMessage:
	def __init__(self,
		message : discord_user.Message,
		username : str = None,
		avatar_url : str = None,
		allowed_mentions = None,
	):
		if isinstance(message, str):
			self.content = message
			self.embeds = []
			self.attachments = []
		else:
			self.content = message.content
			self.embeds = [emb for emb in message.embeds if emb.type != 'gifv' ]
			self.attachments = list(message.attachments)

		self.username = username
		self.avatar_url = avatar_url
		self.allowed_mentions = allowed_mentions

class Config:
	def __init__(self,
		# TODO: Describe sources int, [int] or None for any channels
		sources : int = None,			# Source channels, None means any channel
		destinations = [],# : Union[int, Sequence[int]],
		# TODO: Describa parser params
		parser : Callable[..., bool] = None,
		copy_history : bool = False,		# Copy whole channel history
		only_deleted : bool = False,		# Forward only deleted messages
		restore : bool = True,				# Restore missed messages
		history_depth : datetime = None,	# Point in time from which start copying channel history
		discard_session : bool = False,
	):
		if isinstance(sources, int):
			sources = [ sources ]

		if isinstance(destinations, int):
			destinations = [ destinations ]

		self.sources = sources
		self.destinations = destinations
		self.parser = parser
		self.copy_history = copy_history
		self.only_deleted = only_deleted
		self.restore = restore
		self.history_depth = history_depth
		self.discard_session = discard_session

class Client(discord_user.Client):
	def __init__(
		self,
		token : str,							# Discord account token
		config = [],							# Forward configuration
		debug : bool = False,					# Disable connection
		list_channels : bool = False,			# Show channels list
		presence : discord_user.Status = None,	# User presence to set
		section_name : str = None				# Name of the section in session file
	):
		self.token = token
		self.debug = debug
		self.list_channels = list_channels
		self.config = [cfg for cfg in config if not cfg.only_deleted]
		self.deleted = [cfg for cfg in config if cfg.only_deleted]
		self.forward_ready = []
		self.presence = presence
		self.on_ready_task = None

		# Used as prefix in session file
		self.section_name = section_name if section_name else md5(token.encode()).hexdigest()
		super().__init__()
	
	async def start(self, bot, session):
		self.bot = bot

		key = self.section_name
		if key not in session:
			session[key] = {}
		self.session = session[key]

		for cfg in self.config:
			if cfg.discard_session and cfg.sources:
				for src in cfg.sources:
					self.session[str(src)] = {}

		try:
			if not self.debug:
				await super().start(self.token)
		except asyncio.exceptions.CancelledError:
			self.on_ready_task.cancel()
			await self.close()

	def get_variable(self, src, dst, name):
		# Keys are stored as strings in json
		src = str(src)
		dst = str(dst)
		d = self.session

		if src not in d:
			return None

		d = d[src]
		if dst not in d:
			return None

		return d[dst].get(name)

	def set_variable(self, src, dst, name, value):
		# Keys are stored as strings in json
		src = str(src)
		dst = str(dst)
		self.session.setdefault(src, {}).setdefault(dst, {})[name] = value

	def get_last_msg_id(self, cfg, source):
		start_from = 0	# 0 means no channels

		for dst in cfg.destinations:
			last_id = self.get_variable(source, dst, 'last_msg_id')
			if last_id is None:
				return None

			if not start_from or start_from > last_id:
				start_from = last_id

		return start_from

	async def on_ready(self):
		self.on_ready_task = asyncio.current_task()
		print('Logged on as', self.user)

		try:
			# Set user presence
			if self.presence:
				await self.change_presence(status = self.presence)

			if self.list_channels:
				print_channel_list(self)

			await self.history()
		except GeneratorExit:
			pass

	async def on_message(self, message):
		if not self.bot.is_ready():
			return
		
		channel_id = message.channel.id

		for cfg in self.config:
			if (cfg.sources is not None and channel_id not in cfg.sources) or \
			   channel_id not in self.forward_ready:
				continue

			# Pass message to parser if defined
			parser = cfg.parser
			if parser:
				parsed_msg = await parser(message) if is_async(parser) else parser(message)
				if not parsed_msg:
					continue
			else:
				parsed_msg = message

			for dst in cfg.destinations:
				await self.bot.forward(parsed_msg, dst)
				self.set_variable(channel_id, dst, 'last_msg_id', message.id)

	async def on_message_delete(self, message):
		if not self.bot.is_ready():
			return
		
		for cfg in self.deleted:
			if cfg.sources is not None and \
			   message.channel.id not in cfg.sources or \
			   message.channel.id in cfg.destinations:
				continue

			# Pass message to parser if defined
			parser = cfg.parser
			if parser:
				parsed_msg = await parser(message) if is_async(parser) else parser(message)
				if not parsed_msg:
					continue
			else:
				parsed_msg = message

			for dst in cfg.destinations:
				await self.bot.forward(parsed_msg, dst)

	async def history(self):
		await self.bot.wait_until_ready()

		for cfg in self.config:
			get_history = (cfg.restore or cfg.copy_history) and \
						  not cfg.only_deleted and cfg.sources
			for src in cfg.sources:
				if get_history:
					await self.history_from(cfg, src)
				self.forward_ready.append(src)
				print(f"History from {src} synched")

	async def history_from(self, cfg, source):
			last_id = self.get_last_msg_id(cfg, source)

			# Skip history copying if no messages forwarded before OR no destination channels
			if (not cfg.copy_history and last_id is None) or (last_id == 0):
				return

			ch = self.get_channel(source)
			dst_list = [self.bot.get_channel(dst) for dst in cfg.destinations]
			prev = False

			while prev != last_id:
				prev = last_id
				after = cfg.history_depth if last_id is None else Snowflake(last_id)

				async for msg in ch.history(after = after, oldest_first = True):
					last_id = msg.id

					# Pass message to parser if defined
					parser = cfg.parser
					if parser:
						parsed_msg = await parser(msg) if is_async(parser) else parser(msg)
						if not parsed_msg:
							continue
					else:
						parsed_msg = msg

					for idx, dst_ch in enumerate(dst_list):
						dst_id = cfg.destinations[idx]
						msg_id = self.get_variable(source, dst_id, 'last_msg_id')
						if last_id > (msg_id or 0):
							await self.bot.forward(parsed_msg, dst_ch)
							self.set_variable(source, dst_id, 'last_msg_id', last_id)

import aiohttp
from datetime import datetime

class WebHookChannel():
	def __init__(
		self,
		id : int,
		url : str,
		token : str = None,
	):
		self.id = id
		self.url = url
		self.token = token

	async def send(self,
		content : str,
		embeds = None,
		files = None,
	):
			async with aiohttp.ClientSession() as session:
				hook = discord_bot.Webhook.from_url(self.url, session = session, bot_token=self.token)
				for i in range(1000):
					await hook.send(content = content + datetime.now().strftime( '%Y-%m-%d %H:%M:%S'), username = f"user {i}")
		#discord_webhook.DiscordWebhook()


class WebHookBot():
	def __init__(
		self,
		channels_config : list[WebHookChannel] = [],	# Output channels configuration
		allowed_mentions : discord_bot.AllowedMentions = None,	# Allowed mentions set
	):
		self.channels_config = channels_config
		self.allowed_mentions = allowed_mentions

		self.channels = { ch.id : ch for ch in channels_config }
		
	async def start(self):
		# No task needed
		pass

	def is_ready(self):
		return True

	async def wait_until_ready(self):
		pass

	def get_channel(self, channel_id : int):
		return self.channels[channel_id]

	async def clone_file(self, file):
		f = await file.to_file()
		# Casts discord-self.py File class to discord.py File
		return discord_bot.File(f.fp,
			filename=f.filename,
			description=f.description,
			spoiler=f.spoiler)

	async def forward(self, msg, channel):
		if isinstance(msg, discord_user.Message):
			msg = ParsedWebHookMessage(msg)

		if not isinstance(msg, ParsedWebHookMessage):
			raise TypeError("Invalid message object type.")

		if isinstance(channel, int):
			channel = self.get_channel(channel)

		if not isinstance(channel, WebHookChannel):
			raise TypeError("Invalid channel object type.")

		if not msg.allowed_mentions:
			msg.allowed_mentions = self.allowed_mentions

		# API limits file size to 20MB
		#files = [await self.clone_file(file) for file in msg.attachments if file.size <= 20*1024*1024]
		files = None

		if msg.content or files or msg.embeds:
			# HTTPException: 400 Bad Request (error code: 50006): Cannot send an empty message
			await channel.send(msg.content, embeds = msg.embeds, files = files)


class Bot(discord_bot.Client):
	def __init__(
		self,
		token : str,											# Discord bot token
		list_channels : bool = False,							# Show channels list
		allowed_mentions : discord_bot.AllowedMentions = None,	# Allowed mentions set
		debug : bool = False,									# Disable connection
	):
		self.token = token
		self.list_channels = list_channels
		self.debug = debug

		intents = discord_bot.Intents.default()
		#intents.message_content = True
		super().__init__(intents=intents, allowed_mentions = allowed_mentions)

	async def start(self):
		try:
			if not self.debug:
				await super().start(self.token)
		except asyncio.exceptions.CancelledError as e:
			pass
		# GeneratorExit

		await self.close()

	async def on_ready(self):
		print('Bot logged on as', self.user)

		if self.list_channels:
			print_channel_list(self)

	async def clone_file(self, file):
		f = await file.to_file()
		# Casts discord-self.py File class to discord.py File
		return discord_bot.File(f.fp,
			filename=f.filename,
			description=f.description,
			spoiler=f.spoiler)

	async def forward(self, msg, ch):
		if not self.is_ready():
			return

		if isinstance(ch, int):
			ch = self.get_channel(ch)

		# API limits file size to 8MB
		files = [await self.clone_file(file) for file in msg.attachments if file.size <= 8*1024*1024]
		
		if msg.content or files or msg.embeds:
			# HTTPException: 400 Bad Request (error code: 50006): Cannot send an empty message
			await ch.send(msg.content, embeds = msg.embeds, files = files)


class BotRunner():
	def __init__(self,
		bot,
		sources : list[Config] = [],
		session_file : str = "session.json",
	):
		self.bot = bot
		self.sources = sources
		self.session_file = session_file

		discord_bot.utils.setup_logging(
			handler=discord_bot.utils.MISSING,
			formatter=discord_bot.utils.MISSING,
			level=discord_bot.utils.MISSING
		)

	def run(self):
		try:
			with open(self.session_file, 'r') as f:
				session = json.load(f)
		except FileNotFoundError:
			session = {}

		loop = asyncio.get_event_loop()
		tasks = [loop.create_task(src.start(self.bot, session)) for src in self.sources]
		tasks.append(loop.create_task(self.bot.start(), name='Bot connection'))

		try:
			loop.run_forever()

		except KeyboardInterrupt:
			for task in tasks:
				task.cancel()

		finally:
			print('Closing...')
			for task in tasks:
				loop.run_until_complete(task)

			loop.close()

			with open(self.session_file, 'w', encoding='utf-8') as f:
				json.dump(session, f, ensure_ascii=False, indent=4)
