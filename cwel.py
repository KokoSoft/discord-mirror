import discord_self.discord as discord_user
import discord as discord_bot
import forwarder
import tokens
from channels import *
from parsers import preserve_author, delete_parser
from mod_log_parser import ModLogParser
	
mod_parser = ModLogParser('mod_cwel.log')

sources = [
	forwarder.Client(tokens.G, [	# *
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_GIFY_I_SCREENSHOTY,
			destinations = CHANNEL_ID_CWEL_GIFY_I_SCREENSHOTY,
			parser = preserve_author,
			copy_history = True,
		),
		#forwarder.Config(
		#	sources = CHANNEL_ID_GEJ_SHOTY,
		#	destinations = CHANNEL_ID_CWEL_SHOTY,
		#	parser = preserve_author,
		#	copy_history = True,
		#),
		#forwarder.Config(
		#	destinations = CHANNEL_ID_CWEL_UNCENSORED,
		#	parser = delete_parser,
		#	only_deleted = True
		#),
	], section_name = 'regular', presence = discord_user.Status.invisible),
	#forwarder.Client(tokens.K, [	# @
	#	forwarder.Config(
	#		sources = CHANNEL_ID_GEJ_PODSUMOWANIE_STREAMOW,
	#		destinations = CHANNEL_ID_CWEL_PODSUMOWANIE_STREAMOW,
	#		copy_history = True,
	#		parser = preserve_author,
	#	),
	#	forwarder.Config(
	#		sources = CHANNEL_ID_GEJ_AJEMGE1_SHOTY,
	#		destinations = CHANNEL_ID_CWEL_AJEMGE1_SHOTY,
	#		parser = preserve_author,
	#		copy_history = True,
	#	),
	#	forwarder.Config(
	#		sources = CHANNEL_ID_GEJ_KRONIKA_KRAKOW,
	#		destinations = CHANNEL_ID_CWEL_KRONIKA_KARKOW,
	#		copy_history = True,
	#	),
	#	forwarder.Config(
	#		sources = CHANNEL_ID_GEJ_MOD_LOG,
	#		destinations = CHANNEL_ID_CWEL_MOD_LOG,
	#		parser = mod_parser,
	#		copy_history = True,
	#	),
	#], section_name = 'special', presence = discord_user.Status.invisible)
]

bot = forwarder.Bot(tokens.BOT2, section_name = 'bot',
	allowed_mentions = discord_bot.AllowedMentions(users=False, roles=False))
mod_parser.set_bot(bot)
forwarder.BotRunner(bot, sources, session_file = 'session_cwel.json').run()
