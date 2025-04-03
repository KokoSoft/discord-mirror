import discord_self.discord as discord_user
import discord as discord_bot
import logging
import asyncio
import forwarder
from channels import GUILD_ID_GEJ, GUILD_ID_CWEL
from enum import Enum

logger = logging.getLogger(__name__)

import color_map
import json

class Traitors():
	class Reason(Enum):
		MEMBER_BOTH	= 1	# Member obu serwerów
		GEJ_JOIN	= 2
		GEJ_LEAVE	= 3
		CWEL_JOIN	= 4
		CWEL_LEAVE	= 5

	def __init__(self,
		msg_channel : int,	# Channel to forward traitors messages
		log_channel : int,	# Channel for traitors logs
	):
		self.msg_channel_id = msg_channel
		self.log_channel_id = log_channel
		self.bot = None
		self.client_ready = asyncio.Event()
		super().__init__()

	async def set_client(self, client, guild, members):
		self.client = client
		self.client_guild = guild
		self.client_members = members
		self.client_members_set = set(members.keys())
		self.client_ready.set()

	async def set_bot(self, bot : forwarder.BotBase, guild, members):
		self.bot = bot
		self.bot_guild = guild
		self.bot_members = members
		self.bot_members_set = set(members.keys())

		self.session = bot.session.setdefault('traitors', {})

		self.reported = set(self.session.setdefault('reported', []))
		self.session['reported'] = self.reported

		self.checked = set(self.session.setdefault('checked', []))
		self.session['checked'] = self.checked

		self.msg_channel = await self.bot.get_channel(self.msg_channel_id, webhook = False)
		self.log_channel = await self.bot.get_channel(self.log_channel_id, webhook = False)

		loop = asyncio.get_event_loop()
		self.task = loop.create_task(self.detect())

	async def on_client_join(self, member):
		logger.debug("Client member join %s", str(member))
		if member.id in self.bot_members_set:
			self.reported.add(member.id)
			await self.on_detect(member.id, member, self.Reason.GEJ_JOIN)
		#self.client_members[member.id] = member

	async def on_client_leave(self, member):
		logger.debug("Client member remove %s", str(member))
		if member.id in self.reported:
			self.reported.remove(member.id)
			await self.on_detect(member.id, member, self.Reason.GEJ_LEAVE)
		#self.client_members.pop(member_id, None)

	async def on_bot_join(self, bot_member):
		logger.debug("Bot member join %s", str(bot_member))
		self.bot_members_set.add(bot_member.id)
		if rat := await self.get_member(self.client_guild, bot_member.id):
			self.reported.add(bot_member.id)
			await self.on_detect(bot_member, rat, self.Reason.CWEL_JOIN)
		#self.bot_members[member.id] = member

	async def on_bot_leave(self, member):
		logger.debug("Bot member remove %s", str(member))
		self.bot_members_set.discard(member.id)
		if member.id in self.reported:
			self.reported.remove(member.id)
			await self.on_detect(member, member.id, self.Reason.CWEL_LEAVE)

	# Get roles
	@staticmethod
	def get_roles(member, colors = False, past = False):
		nobody = '<był nikim>' if past else '<jest nikim>'
		roles = member.roles[1:]
		return ' '.join([
			f'[{emoji}{name}]'
			for emoji, name in [
			(f'{role.unicode_emoji} ' if role.unicode_emoji else '',
			color_map.closest_discord_color(role.color.to_rgb(), role.name) if colors else role.name)
			for role in roles]
		]) if roles else nobody

	# On message
	async def on_message(self, message : discord_user.Message):
		if not self.bot:
			return
		if not message.author.id in self.bot_members_set:
			return

		if '://tenor.com/' in message.content:
			return

		msg = forwarder.ParsedMessage(message)
		msg.content = f'{message.channel.name}     {self.get_roles(message.author)}     {message.author.mention}: {message.clean_content}'[:2000]
		await self.bot.forward(msg, self.msg_channel)

	@staticmethod
	async def get_member(guild, member_id):
		if not (member := guild.get_member(member_id)):
			try:
				member = await guild.fetch_member(member_id)
			except (discord_user.NotFound, discord_bot.NotFound):
				pass
			except Exception as e:
				logger.error('Fetch exception %s: %s', type(e), e)
		return member

	# Detect
	async def detect(self):
		try:
			await self._detect()
		except Exception:
				logger.exception('Exception in detect task')

	# Internal detect
	async def _detect(self):
		await self.client_ready.wait()

		logger.debug('Detecting rats...')
		traitors_set = (self.client_members_set & self.bot_members_set) - self.reported
		for traitor_id in traitors_set:
			rat = self.client_members[traitor_id]
			bm = self.bot_members[traitor_id]
			logger.warning('Rat detected %s, stage %d', rat, 0)
			self.reported.add(rat.id)
			await self.on_detect(bm, rat, self.Reason.MEMBER_BOTH)
		self.client_members = None

		for bm in self.bot_members.values():
			if bm.id in self.reported or bm.id in traitors_set or bm.id in self.checked:
				continue

			logger.debug('Checking %s (ID: %d)', bm.name, bm.id)

			stage = 1
			if not (rat := self.client_guild.get_member(bm.id)):
				try:
					stage = 2
					rat = await self.client_guild.fetch_member(bm.id)
				except discord_user.NotFound:
					self.checked.add(bm.id)
					continue
				except Exception as e:
					logger.error('Fetch exception %s: %s', type(e), e)
					continue

			logger.warning('Rat detected %s, stage %d', rat, stage)
			self.reported.add(rat.id)
			await self.on_detect(bm, rat, self.Reason.MEMBER_BOTH)

		logger.info('Traitors detect done.')
		self.bot_members = None

	# Rat detected
	async def on_detect(self, bot_member, client_member, reason : Reason):
		if isinstance(bot_member, int):
			bot_member : discord_bot.Member = await self.get_member(self.bot_guild, bot_member)

		if isinstance(client_member, int):
			client_member : discord_user.Member = await self.get_member(self.client_guild, client_member)

		match reason:
			case self.Reason.MEMBER_BOTH:
				msg = '{} (login: `{}`) jest szczurem znanym jako **{}**!```ansi\nU nas: {}, tam: {}```'.format(
					bot_member.mention, bot_member.name, client_member.display_name,
					self.get_roles(bot_member, True), self.get_roles(client_member, True))

			case self.Reason.GEJ_JOIN:
				msg = '{} (login: `{}`) wybrał życie zdrajcy!```ansi\nU nas: {}```'.format(
					bot_member.mention, bot_member.name, self.get_roles(bot_member, True))

			case self.Reason.GEJ_LEAVE:
				msg = '{} (login: `{}`) męczony wyrzutami sumienia przestał zdradzać lub po prostu wyłapał bana.```ansi\nU nas: {}, tam był {}```'.format(
					bot_member.mention, bot_member.name, self.get_roles(bot_member, True), self.get_roles(client_member, True, past = True))

			case self.Reason.CWEL_JOIN:
				msg = 'Przyszedł do nas kret {} (login: `{}`) znany jako **{}**!```ansi\nTam: {}```'.format(
					bot_member.mention, bot_member.name, client_member.display_name, self.get_roles(client_member, True))

			case self.Reason.CWEL_LEAVE:
				msg = 'Kret **{}** {} (login: `{}`) opuścił pokład, chuj mu w dupe.```ansi\nU nas był: {}, tam: {}```'.format(
					bot_member.display_name, client_member.mention, client_member.name,
					self.get_roles(bot_member, True, past = True), self.get_roles(client_member, True))

		await self.log_channel.send(msg)

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
		if not guild:
			logger.error('Unable to get gej guild')
			return
		
		members = await guild.fetch_members()
		members = { member.id : member for member in members }
		await self.traitors.set_client(self, guild, members)

	async def on_member_join(self, member):
		if member.guild.id == GUILD_ID_GEJ:
			await self.traitors.on_client_join(member)

	async def on_raw_member_remove(self, payload):
		if payload.guild_id == GUILD_ID_GEJ:
			await self.traitors.on_client_leave(payload.user)

	async def on_member_remove(self, member):
		return
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

		members1 = set()
		for member in guild.members:
			members1.add(member.id)

		members2 = set()
		async for member in guild.fetch_members():
			members2.add(member.id)

		print(members1 - members2)
		print(members2 - members1)

		#mem = {'members' : members1, 'fetch_members' : members2 }
		#with open('bot_members.json', 'w', encoding='utf-8') as f:
		#	json.dump(mem, f, ensure_ascii=False, indent=4)

		await self.traitors.set_bot(self, guild, members)

	async def on_member_join(self, member):
		logger.debug('Bot Join %s %d %d', str(member), member.id, member.guild.id)
		if member.guild.id == GUILD_ID_CWEL:
			await self.traitors.on_bot_join(member)

	async def on_raw_member_remove(self, payload):
		if payload.guild_id == GUILD_ID_CWEL:
			await self.traitors.on_bot_leave(payload.user)

	async def on_member_remove(self, member):
		return
		await self.traitors.on_bot_leave(member.id)
