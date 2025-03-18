import forwarder
import discord
from datetime import datetime, timedelta
import tokens
from channels import *
import parsers
from mod_log_parser import ModLogParser
	
mod_parser = ModLogParser('mod.log')

sources = [
	forwarder.Client(tokens.G, [	# *
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_GIFY_I_SCREENSHOTY,
			destinations = CHANNEL_ID_TEST_GIFY_I_SCREENSHOTY,
			parser = parsers.drop_embeds,
			copy_history = True,
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_SHOTY,
			destinations = CHANNEL_ID_TEST_SHOTY,
			parser = parsers.drop_embeds,
			copy_history = True,
		),
		forwarder.Config(
			destinations = CHANNEL_ID_TEST_UNCENSORED,
			parser = parsers.delete_parser,
			only_deleted = True
		),
	], section_name = "regular", debug = False, presence = discord.Status.invisible),
	forwarder.Client(tokens.K, [	# @
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_PODSUMOWANIE_STREAMOW,
			destinations = CHANNEL_ID_TEST_PODSUMOWANIE_STREAMOW,
			copy_history = True,
			parser = parsers.preserve_author,
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_AJEMGE1_SHOTY,
			destinations = CHANNEL_ID_TEST_AJEMGE1_SHOTY,
			parser = parsers.drop_embeds,
			copy_history = True,
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_KRONIKA_KRAKOW,
			destinations = CHANNEL_ID_TEST_KRONIKA_KARKOW,
			copy_history = True,
			#history_depth = datetime.utcnow() - timedelta(days = 2),#weeks=4)
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_MOD_LOG,
			destinations = CHANNEL_ID_TEST_MOD_LOG,
			parser = mod_parser,
			copy_history = True,
			#discard_session = True,
			#history_depth = datetime.utcnow() - timedelta(days = 2),#weeks=4) hours=20
		),
	], section_name = "special", debug = False, list_channels = False, presence = discord.Status.invisible)
]

bot = forwarder.Bot(tokens.BOT, sources,
	allowed_mentions = discord.AllowedMentions(users=False, roles=False),
	debug = False,
	list_channels = False)
mod_parser.set_bot(bot)
bot.run()
