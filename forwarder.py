from typing import Sequence, Union, NewType
from collections.abc import Callable, Awaitable
import discord as discord_bot
import discord_self as discord_user
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
# The original message is stored in a discord.py cache and its passed to on_message_delete 
class ParsedMessage:
	def __init__(self,
		message : discord_user.Message | str,
	):
		self.content = self.webhook_content = message.clean_content
		self.embeds = [emb for emb in message.embeds if emb.type == 'rich' ]
		self.attachments = list(message.attachments)
		self.username = message.author.display_name
		self.avatar_url = message.author.avatar.url if message.author.avatar else None
		super().__init__()


# Use this class to copy received message for a WebHook.
# The original message is stored in a discord.py cache
class ParsedWebHookMessage:
	def __init__(self,
		message : discord_user.Message | str,
		username : str = None,
		avatar_url : str = None,
		allowed_mentions = None,
	):
		if isinstance(message, discord_user.Message):
			self.content = message.content
			self.embeds = [ emb for emb in message.embeds if emb.type == 'rich' ]
			self.attachments = list(message.attachments)
			self.username = message.author.display_name
			self.avatar_url = message.author.avatar.url if message.author.avatar else None
		else:
			#if isinstance(message, str):
			self.content = message
			self.embeds = []
			self.attachments = []
			self.content = message.content
			self.username = username
			self.avatar_url = avatar_url

		self.allowed_mentions = allowed_mentions

Sendable = NewType('Sendable', Union[ParsedMessage, discord_user.Message])
SyncParserCallback = NewType('SyncParserCallback',
	Callable[[discord_user.Client, discord_user.message.Message], Sendable])

AsyncParserCallback = NewType('AsyncParserCallback',
	Awaitable[[discord_user.Client, discord_user.Message], Sendable])

ParserCallback = NewType('ParserCallback', Union[SyncParserCallback, AsyncParserCallback])

class Config:
	def __init__(self,
		sources : int | Sequence[int] | None = None,	# Source channels, None means any channel
		destinations : int | Sequence[int] | None = [],	# List of destination channels
		parser : ParserCallback | None = None,			# Function used to parse a message before forward
		copy_history : bool = False,					# Copy whole channel history
		only_deleted : bool = False,					# Forward only deleted messages
		restore : bool = True,							# Restore missed messages
		history_depth : datetime | None = None,			# Point in time from which start copying channel history
		discard_session : bool = False,					# Ignore session data stored in file
		debug : bool = False,
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

# SessionStore class
class SessionStore():
	def __init__(self):
		super().__init__()

	def session_setup(self, session, key):
		if key not in session:
			session[key] = {}
		self.session = session[key]

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

# Client class
class Client(discord_user.Client, SessionStore):
	DEBUG_NO_HISTORY	= 1
	DEBUG_NO_RECV		= 2
	DEBUG_NO_CONNECT	= 3

	def __init__(
		self,
		token : str,							# Discord account token
		config = [],							# Forward configuration
		debug : bool = False,					# Debug level
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
		self.session_setup(session, self.section_name)

		for cfg in self.config:
			if cfg.discard_session and cfg.sources:
				for src in cfg.sources:
					self.session[str(src)] = {}

		try:
			if self.debug < self.DEBUG_NO_CONNECT:
				await super().start(self.token)
		except asyncio.exceptions.CancelledError:
			self.on_ready_task.cancel()
			await self.close()

	# Get last message id
	def get_last_msg_id(self, cfg, source):
		start_from = 0	# 0 means no channels

		for dst in cfg.destinations:
			last_id = self.get_variable(source, dst, 'last_msg_id')
			if last_id is None:
				return None

			if not start_from or start_from > last_id:
				start_from = last_id

		return start_from

	# On Client ready
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

	# On message
	async def on_message(self, message):
		if not self.bot.is_ready() or self.debug >= self.DEBUG_NO_RECV:
			return
		
		channel_id = message.channel.id

		for cfg in self.config:
			if (cfg.sources is not None and channel_id not in cfg.sources) or \
			   channel_id not in self.forward_ready:
				continue

			# Pass message to parser if defined
			parser = cfg.parser
			if parser:
				parsed_msg = await parser(self, message) if is_async(parser) \
					else parser(self, message)
				if not parsed_msg:
					continue
			else:
				parsed_msg = message

			for dst in cfg.destinations:
				await self.bot.forward(parsed_msg, dst)
				self.set_variable(channel_id, dst, 'last_msg_id', message.id)

	# On message deleted
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
				parsed_msg = await parser(self, message) if is_async(parser) \
					else parser(self, message)
				if not parsed_msg:
					continue
			else:
				parsed_msg = message

			for dst in cfg.destinations:
				await self.bot.forward(parsed_msg, dst)

	# History thread
	async def history(self):
		if self.debug >= self.DEBUG_NO_HISTORY:
			return

		await self.bot.wait_until_ready()

		for cfg in self.config:
			get_history = (cfg.restore or cfg.copy_history) and \
						  not cfg.only_deleted and cfg.sources
			for src in cfg.sources:
				if get_history:
					await self.history_from(cfg, src)
				self.forward_ready.append(src)
				print(f"History from {src} synched")

	# Read message history from a channel
	async def history_from(self, cfg, source):
			last_id = self.get_last_msg_id(cfg, source)

			# Skip history copying if no messages forwarded before OR no destination channels
			if (not cfg.copy_history and last_id is None) or (last_id == 0):
				return

			src_ch = self.get_channel(source)
			dst_list = [await self.bot.get_channel(dst) for dst in cfg.destinations]
			prev = False

			while prev != last_id:
				prev = last_id
				after = cfg.history_depth if last_id is None else Snowflake(last_id)

				async for msg in src_ch.history(after = after, oldest_first = True):
					last_id = msg.id

					# Pass message to parser if defined
					parser = cfg.parser
					if parser:
						parsed_msg = await parser(self, msg) if is_async(parser) \
							else parser(self, msg)
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

async def on_request_start(session, context, params):
	logging.getLogger('aiohttp.client').debug(f'Starting request <{params}>')

class LoggingClientSession(aiohttp.ClientSession):
	async def _request(self, method, url, **kwargs):
		print('Starting request ', method, url, kwargs)
		resp = await super()._request(method, url, **kwargs)
		print('Response', resp)
		return resp

# WebHookChannel class
class WebHookChannel():
	def __init__(self, id : int, url : str):
		self.id = id
		self.url = url

	async def setup(self, session, token):
		print('setup')
		self.hook = discord_bot.Webhook.from_url(
			self.url,
			session = session,
			bot_token = token)

		if token:
			print('fetch', self.hook.is_authenticated())
			self.hook = await self.hook.fetch()
		print('done', self.hook.is_authenticated())

	async def send(self,
		content : ParsedWebHookMessage,
		embeds = None,
		files = None,
	):
				#discord.errors.Forbidden: 403 Forbidden (error code: 50013): Missing Permissions
			#for i in range(1000):
				await self.hook.send(
					content = content.content+ datetime.now().strftime( '%Y-%m-%d %H:%M:%S'),
					embeds = content.embeds,
					files = content.attachments,
					allowed_mentions = content.allowed_mentions,
					username = content.username,
					avatar_url = content.avatar_url
				)

				

# WebHookBot class
class WebHookBot():
	def __init__(
		self,
		channels_config : list[WebHookChannel] = [],			# Output channels configuration
		allowed_mentions : discord_bot.AllowedMentions = None,	# Allowed mentions set
		token : str = None,										# Bot token to authorize WebHooks (optional, allows high rate)
	):
		self.channels_config = channels_config
		self.allowed_mentions = allowed_mentions
		#self.token = token
		self.channels = { ch.id : ch for ch in channels_config }
		self.session = None
		self.token = token
		self.ready: asyncio.Event = asyncio.Event()
		super().__init__()

	def __del__(self):
		print("Destructor called")
		if self.session:
			self.session.close()

	async def start(self):
		self.session = LoggingClientSession()

		for ch in self.channels_config:
			await ch.setup(self.session, self.token)

		self.ready.set()

	def is_ready(self):
		return self.ready is not None and self.ready.is_set()

	async def wait_until_ready(self):
		if self.ready:
			await self.ready.wait()

	async def get_channel(self, channel_id : int):
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
			channel = await self.get_channel(channel)

		if not isinstance(channel, WebHookChannel):
			raise TypeError("Invalid channel object type.")

		if not msg.allowed_mentions:
			msg.allowed_mentions = self.allowed_mentions

		# API limits file size to 20MB
		msg.attachments = [await self.clone_file(file) for file in msg.attachments if file.size <= 20*1024*1024]
		files = None

		if msg.content or msg.attachments or msg.embeds:
			#if isinstance(channelWebHookChannel
			# HTTPException: 400 Bad Request (error code: 50006): Cannot send an empty message
			await channel.send(msg)#.content, embeds = msg.embeds, files = files)

HookableChannel = Union[discord_bot.TextChannel, discord_bot.VoiceChannel, discord_bot.StageChannel, discord_bot.ForumChannel]

# Bot class
class Bot(discord_bot.Client, SessionStore):
	DEBUG_NO_SEND		= 1
	DEBUG_NO_CONNECT	= 2
	def __init__(
		self,
		token : str,											# Discord bot token
		list_channels : bool = False,							# Show channels list
		allowed_mentions : discord_bot.AllowedMentions = None,	# Allowed mentions set
		section_name : str = None,								# Name of the section in session file
		debug : int = 0,										# Debug level
		use_webhooks : bool = True,								# Use WebHooks to post messages (allows set nickname)
	):
		self.token = token
		self.list_channels = list_channels
		self.use_webhooks = use_webhooks
		self.debug = debug
		self.webhooks = {}

		self.attachment_size_limit = 8 * 1024 * 1024

		# Used as prefix in session file
		self.section_name = section_name if section_name else md5(token.encode()).hexdigest()

		intents = discord_bot.Intents.default()
		intents.webhooks = use_webhooks
		#intents.message_content = True
		super().__init__(intents=intents, allowed_mentions = allowed_mentions)

	# Thread start
	async def start(self, session):
		self.session_setup(session, self.section_name)

		try:
			if self.debug < self.DEBUG_NO_CONNECT:
				await super().start(self.token)
		except asyncio.exceptions.CancelledError as e:
			pass
		# GeneratorExit
		self.store_webhooks()
		await self.close()

	# On Bot ready
	async def on_ready(self):
		print('Bot logged on as', self.user)

		if self.list_channels:
			print_channel_list(self)

		if self.use_webhooks:
			if True:
				self.retrieve_webhooks()
			else:
				await self.configure_webhooks(install_all = True)

	# Store WebHooks tokens in session file
	def store_webhooks(self):
		for channel_id, hook in self.webhooks.items():
			self.set_variable('webhooks', channel_id, 'token', hook.token)
			self.set_variable('webhooks', channel_id, 'name', hook.name)

	# Load WebHooks from session file
	def retrieve_webhooks(self):
		if 'webhooks' in self.session:
			for channel_id in self.session['webhooks']:
				token = self.get_variable('webhooks', channel_id, 'token')
				name = self.get_variable('webhooks', channel_id, 'name')
				hook = discord_bot.Webhook.from_url(
					f'https://discord.com/api/webhooks/{channel_id}/{token}',
					client = self)
				hook.name = name
				self.webhooks[channel_id] = hook

	# Fetch all WebHooks and optionally create a missing WebHooks
	async def configure_webhooks(self, install_all : bool = False):
		for guild in self.guilds:
			if not install_all:
				hooks = await guild.webhooks()
				webhooks = { h.channel_id : h for h in hooks }
				self.webhooks.update(webhooks)
				continue

			for channel in guild.channels:
					if not isinstance(channel, HookableChannel):
						continue

					hooks = await channel.webhooks()
					self.webhooks[channel.id] = hooks[0] if hooks \
						else await self.create_webhook(channel)

		print('WebHooks configured.')

	# On WebHooks update
	async def on_webhooks_update(self, channel):
		print(f'WebHooks for {channel.name} (ID: {channel.id} updated.')

	# Create new WebHook
	async def create_webhook(self, channel : HookableChannel):
			print(f'Creating WebHook for channel {channel.name} (ID: {channel.id})')
			return await channel.create_webhook(
				name = "Content Mirror Bot",
				reason = "Automatically created WebHook for the bot needs.")

	# Get channel WebHook
	async def get_channel_webhook(self, channel_id : int):
		if channel_id in self.webhooks:
			return self.webhooks[channel_id]

		channel = super().get_channel(channel_id)
		if not channel:
			return None

		hooks = await channel.webhooks()
		if hooks:
			hook = hooks[0]
		else:
			hook = await self.create_webhook(channel)

		self.webhooks[channel_id] = hook
		return hook

	# Clone file object
	async def clone_file(self, file):
		f = await file.to_file()
		# Casts discord-self.py File class to discord.py File
		return discord_bot.File(f.fp,
			filename=f.filename,
			description=f.description,
			spoiler=f.spoiler)

	# Get channel
	async def get_channel(self, channel_id : int):
		if self.use_webhooks:
			return await self.get_channel_webhook(channel_id)
		else:
			return super().get_channel(channel_id)

	# Send message
	async def forward(self, message, channel):
		if not self.is_ready() and \
		   self.debug < self.DEBUG_NO_CONNECT and \
		   not self.use_webhooks:
			return

		if isinstance(channel, int):
			channel = await self.get_channel(channel)

		# API limits file size. Send too big files as url
		files = []
		files_url = []
		for file in message.attachments:
			if file.size <= self.attachment_size_limit:
				files.append(await self.clone_file(file))
			else:
				files_url.append(file.url)
		message.attachments = files

		# HTTPException: 400 Bad Request (error code: 50006): Cannot send an empty message
		content = [message.content, message.webhook_content][isinstance(channel, discord_bot.Webhook)]
		if content or files or message.embeds:
			await self.send(channel, message)

		if files_url:
			message.embeds = discord_bot.utils.MISSING
			message.attachments = discord_bot.utils.MISSING
			for url in files_url:
				print('Too big', url)
				message.content = message.webhook_content = url
				await self.send(channel, message)

	# Sends message via Bot connection or WebHook
	async def send(self, channel, message):
		if self.debug >= self.DEBUG_NO_SEND:
			return

		if isinstance(channel, discord_bot.Webhook):
			await channel.send(
				content = message.webhook_content,
				embeds = message.embeds,
				files = message.attachments,
				allowed_mentions = self.allowed_mentions,
				username = message.username,
				avatar_url = message.avatar_url)
		else:
			await channel.send(
				message.content,
				embeds = message.embeds,
				files = message.attachments)

# BotRunner class
class BotRunner():
	def __init__(self,
		bot,
		sources : list[Config] = [],
		session_file : str = "session.json",
		log_level = discord_bot.utils.MISSING
	):
		self.bot = bot
		self.sources = sources
		self.session_file = session_file

		discord_bot.utils.setup_logging(
			handler = discord_bot.utils.MISSING,
			formatter = discord_bot.utils.MISSING,
			level = log_level
		)

	def run(self):
		try:
			with open(self.session_file, 'r') as f:
				session = json.load(f)
		except FileNotFoundError:
			session = {}

		loop = asyncio.get_event_loop()
		tasks = [loop.create_task(src.start(self.bot, session)) for src in self.sources]
		tasks.append(loop.create_task(self.bot.start(session), name='Bot connection'))

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
