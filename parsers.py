from forwarder import ParsedMessage, Client
import discord_self.discord as discord_user
import discord as discord_bot

async def get_referenced_message(client : discord_user.Client,
						   reference : discord_user.MessageReference):
	if reference.cached_message:
		return reference.cached_message

	channel = client.get_channel(reference.channel_id)
	try:
		return await channel.fetch_message(reference.message_id)
	except discord_user.errors.NotFound:
		return None
	#print(message.content, message.clean_content, message.embeds, message.attachments, message.type, message.reference)
	# MessageType.reply
	#if False and message.reference and message.type == discord_user.MessageType.default:
	#	print(f"Reference ch: {message.reference.channel_id} id: {message.reference.message_id}")
	#	m = await get_referenced_message(client, message.reference)
	#	if m:
	#		print('	ref msg:', m, m.author, m.author.name, m.author.display_name)
	#	else:
	#		print('	MISSING REF MESSAGE');
	#return #None

def is_spam(message, allow_bot : bool = False):
	content = message.content.casefold()
	if message.author.bot and not allow_bot or \
		'discord.gg/'.casefold() in content or \
		'1178301953718095943'.casefold() in content:
		print(f"Spam! '{content}' app: {message.application_id} hook: {message.webhook_id} bot: {message.author.bot}")
		return True
	return False

def preserve_author(client : Client, message : discord_user.Message, allow_bot : bool = False):
	if message.type in [discord_user.MessageType.thread_created,
						discord_user.MessageType.member_join,
						discord_user.MessageType.poll_result] or \
	   is_spam(message, allow_bot):
		return

	msg = ParsedMessage(message)
	if len(msg.content) > 2000:
		print('Content too long!', message)
		return

	#if msg.content:
	content = f"**{message.author.name}**: {msg.content}"
	if len(msg.content) <= 2000:
		msg.content = content

	if message.type != discord_user.MessageType.default and message.type != discord_user.MessageType.reply:
		print(f"Interesting message type {message.type}, ID: {message.id}, Content: {message.content}")

	# Don't forward original message if it is reply
	forwarded = False
	if message.type == discord_user.MessageType.default:
		for msg_snap in message.message_snapshots:
			snap = ParsedMessage(msg_snap)
			content = client.clean_content(msg_snap.content)
			snap.webhook_content = content
			snap.content = f"**{message.author.name}**: {content}"
			if not msg_snap.cached_message:
				snap.username = message.author.name
				snap.avatar_url = message.author.avatar.url if message.author.avatar else None

			forwarded = True
			yield snap
			
	if message.content or message.attachments or message.embeds or message.poll:
		yield msg
	else:
		if not forwarded and not message.stickers:
			print('Empty message!', message)

	# Forward stickers as urls
	for sticker in message.stickers:
		msg.content = sticker.url
		msg.webhook_content = sticker.url
		msg.embeds = discord_bot.utils.MISSING
		msg.attachments = []
		print(f'Sticker "{sticker.name}", id: {sticker.id}, url: {sticker.url}')
		yield msg


def delete_parser_emb(client, message):
	for msg in preserve_author(client, message):
		embed = discord_user.Embed(
			description = f'Usunięto z: {message.channel.name}',
			timestamp = message.created_at).set_footer(text = 'Wysłano')
		msg.embeds.append(embed)
		yield msg

def delete_parser(client, message):
	timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
	username = f"{message.author.name}     {message.channel.name}     {timestamp}"

	for msg in preserve_author(client, message):
		msg.username = username
		msg.content = f"**{message.author.name}** on **{message.channel.name}** at {timestamp} *deleted message*:\n{message.content}"
		yield msg

def as_embed(client, msg):
	emb = discord_bot.Embed(description = msg.content, color = msg.author.colour.value)
	emb.set_author(name = msg.author.display_name, icon_url = msg.author.display_avatar.url)
	msg.embeds.insert(0, emb)
	msg.content = None
	return msg

import re

def delete_parser_tmp(client, message):
	header, _, content = message.content.partition(':\n')
	f = re.findall(r'\*\*(.*?)\*\*', header)
	channel = f[0]
	user = f[1]
	
	timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
	username = f"{user}     {channel}     {timestamp}"
	message.embeds = []

	print(user, channel, content)
	for msg in preserve_author(client, message, True):
		msg.username = username
		msg.content = content
		msg.webhook_content = content
		yield msg


	return None
