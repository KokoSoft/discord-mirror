from zoneinfo import ZoneInfo
import discord_self.discord as discord_user
from datetime import datetime, timedelta
import tokens
from channels import *
import asyncio
import forwarder
from parsers import preserve_author, delete_parser, wonsik_filter
from logging import handlers
import logging

forwarder.time_zone = ZoneInfo("Europe/Warsaw")

logger = logging.getLogger()
udp_handler = logging.handlers.DatagramHandler('127.0.0.1', tokens.LOGGER_PORT)
logging.getLogger("forwarder").setLevel(logging.DEBUG)

logger.setLevel(logging.DEBUG)#INFO)
logger.addHandler(udp_handler)

class UploadClient(forwarder.Client):
	def __init__(
		self,
		token : str,														# Discord account token
		file_name : str = None,												# Dump entries to specified file
		config = [],														# Forward configuration
		debug : bool = False,												# Debug level
		list_channels : bool = False,										# Show channels list
		presence : discord_user.Status = discord_user.Status.invisible,		# User presence to set
		section_name : str = None											# Name of the section in session file
	):
		super().__init__(token, config, debug, list_channels, presence, section_name)
		with open(file_name, 'r', encoding='utf-8') as file:
			self.input = [[int(x) for x in line.rstrip().split(' ')] for line in file]
		self.input.sort()

	async def history(self):
		logger.debug('History')
		last_id = None
		cnt = 0
		for message_id, channel_id in self.input:
			if last_id == message_id:
				logger.warning('Skipping %d', message_id)
				continue

			last_id = message_id
			if cnt % 50 == 0:
				logger.info('%d. Sending %d in %d', cnt, message_id, channel_id)

			channel = self.get_channel(channel_id)
			message = await channel.fetch_message(message_id)

			for msg in self.parse(message):
				await self.bot.forward(msg, 1)
			cnt += 1

		logger.info('Done! :) Uploaded %d messages.', cnt)

	def parse(self, message):
		timestamp = message.created_at.astimezone(forwarder.time_zone).strftime('%Y-%m-%d %H:%M:%S')
		username = f"{message.author.display_name}     {message.channel.name}     {timestamp}"

		for msg in preserve_author(self, message):
			msg.username = username
			msg.content = f"**{message.author.name}** on **{message.channel.name}** at {timestamp} *deleted message*:\n{message.content}"
			yield msg

wonsik = UploadClient(tokens.L, 'wonsik.txt')
bot = forwarder.WebHookBot([
	(1, tokens.CHANNEL_HOOK_TEST_DEVELOPER_TESTS),
	(2, tokens.CHANNEL_HOOK_CWEL_GEJOWSKIE_WIADOMOSCI)
	])
runner = forwarder.BotRunner(bot, [ wonsik ], session_file = None)
logging.getLogger('discord_self').setLevel(logging.INFO)
logging.getLogger('discord').setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
runner.run()

