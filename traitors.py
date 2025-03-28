import discord_self.discord as discord_user
import discord as discord_bot
import logging
import asyncio
import forwarder
from channels import GUILD_ID_GEJ, GUILD_ID_CWEL

logger = logging.getLogger(__name__)


import json

class Traitors():
	def __init__(self,
		msg_channel : int,	# Channel to forward traitors messages
		log_channel : int,	# Channel for traitors logs
	):
		self.msg_channel_id = msg_channel
		self.log_channel_id = log_channel
		self.client_ready = asyncio.Event()
		super().__init__()

	async def set_client(self, client, members):
		self.client = client
		self.client_members = members
		self.client_ready.set()
		#members = [(m.id, m.name, m.display_name) for _, m in members.items()]
		#with open('client.json', 'w', encoding='utf-8') as f:
		#		json.dump(members, f, ensure_ascii=False, indent=4)

	async def set_bot(self, bot : forwarder.BotBase, members):
		self.bot = bot
		#self.bot_members = members
		self.bot_members_set = set(members.keys())

		self.msg_channel = await self.bot.get_channel(self.msg_channel_id, webhook = False)
		self.log_channel = await self.bot.get_channel(self.log_channel_id, webhook = False)

		loop = asyncio.get_event_loop()
		self.task = loop.create_task(self.detect())
		#members = [(m.id, m.name, m.display_name) for _, m in members.items()]

		#with open('bot.json', 'w', encoding='utf-8') as f:
		#		json.dump(members, f, ensure_ascii=False, indent=4)

	async def on_client_join(self, member):
		logger.info("Client member join %s", str(member))
		#self.client_members[member.id] = member

	async def on_client_leave(self, member_id):
		logger.info("Client member remove %d", member_id)
		#self.client_members.pop(member_id, None)

	async def on_bot_join(self, member):
		logger.info("Bot member join %s", str(member))
		self.bot_members_set.add(member.id)
		#self.bot_members[member.id] = member

	async def on_bot_leave(self, member_id):
		logger.info("Bot member remove %s", str(member_id))
		self.bot_members_set.discard(member_id)
		pass

	async def parse_msg():
		pass

	async def on_message(self, message : discord_user.Message):
		if not message.author.id in self.bot_members_set:
			return

		msg = forwarder.ParsedMessage(message)
		msg.content = f'{message.channel.name}     {message.author.mention}: {message.clean_content}'[:2000]
		await self.bot.forward(msg, self.msg_channel)
		'''if msg:
		await self.bot.forward(parsed_msg, self.msg_channel)

		# Pass message to parser if defined
		parser = None
		if parser:
			parsed_msg = await parser(self, message) if is_async(parser) \
				else parser(self, message)
			if not parsed_msg:
				return
		else:
			parsed_msg = message'''

	async def detect(self):
		await self.client_ready.wait()
		logger.debug('detect ready')

		#for member in self.bot_members:
		#	print(member, self.bot_members[member])
		#	if member in self.client_members:
		#		traitor = self.client_members[member]
		#		logger.warning('Traitor detected %s', traitor)

class Client(forwarder.Client):
	def __init__(
		self,
		token : str,							# Discord account token
		traitors : Traitors,
		config = [],							# Forward configuration
		debug : bool = False,					# Debug level
		list_channels : bool = False,			# Show channels list
		presence : discord_user.Status = None,	# User presence to set
		section_name : str = None				# Name of the section in session file
	):
		self.traitors : Traitors = traitors
		super().__init__(token, config, debug, list_channels, presence, section_name)

	async def on_ready(self):
		await self.list_users()
		await super().on_ready()

	# On message
	async def on_message(self, message):
		if not self.bot.is_ready() or self.debug >= self.DEBUG_NO_RECV:
			return

		await super().on_message(message)
		await self.traitors.on_message(message)

	async def list_users(self):
		guild = self.get_guild(GUILD_ID_GEJ)
		#if not guild:
		#	logger.error('Unable to get gej guild')
		#	return
		#
		#members = await guild.fetch_members()
		#members = { member.id : member for member in members }
		members = None
		await self.traitors.set_client(self, members)

	async def on_member_join(self, member):
		# jaki guild??
		await self.traitors.on_client_join(member)

	async def on_raw_member_remove(self, payload):
		if payload.guild_id != GUILD_ID_GEJ:
			return
		logger.info("Client member raw remove %s", str(payload))
		await self.traitors.on_client_leave(payload.user.id)

	async def on_member_remove(self, member):
		await self.traitors.on_client_leave(member.id)

class Bot(forwarder.Bot):
	def __init__(
		self,
		token : str,											# Discord bot token
		traitors : Traitors,
		list_channels : bool = False,							# Show channels list
		allowed_mentions : discord_bot.AllowedMentions = None,	# Allowed mentions set
		section_name : str = None,								# Name of the section in session file
		debug : int = 0,										# Debug level
		use_webhooks : bool = True,								# Use WebHooks to post messages (allows set nickname)
		dump_webhooks : bool = False,							# Dump all configured WebHooks
		preconfigure_webhooks : bool = False,					# Add WebHooks to all channels
	):
		self.traitors : Traitors = traitors

		intents = discord_bot.Intents.default()
		intents.members = True
		super().__init__(token, list_channels, allowed_mentions, section_name,
						 debug, use_webhooks, dump_webhooks, preconfigure_webhooks, intents)

	async def on_ready(self):
		await self.list_users()
		await super().on_ready()

	async def list_users(self):
		guild = self.get_guild(GUILD_ID_CWEL)
		if not guild:
			logger.error('Unable to get cwel guild')
			return

		if guild.chunked:
			logger.debug('Guild is chunked, nice :)')
			members = { member.id : member for member in guild.members }
		else:
			logger.debug('Fetching guild members...')
			async for member in guild.fetch_members():
				members[member.id] = member

		await self.traitors.set_bot(self, members)

	async def on_member_join(self, member):
		await self.traitors.on_bot_join(member)

	async def on_raw_member_remove(self, payload):
		logger.info("Member raw remove %s", str(payload))
		await self.traitors.on_bot_leave(payload.user.id)

	async def on_member_remove(self, member):
		await self.traitors.on_bot_leave(member.id)
