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

def preserve_author(client : Client , message : discord_user.Message):
	if message.type == discord_user.MessageType.thread_created:
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
			
	if message.content or message.attachments or message.embeds:
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



def drop_embeds(client, message):
	message.embeds = []
	return message

def delete_parser(client, message):
	msg = ParsedMessage(message)
	content = message.clean_content
	msg.content = f"*From* **{message.channel.name}** *deleted* **{message.author.display_name}** *message*:\n{message.content}"
	return msg


def as_embed(client, msg):
	emb = discord_bot.Embed(description = msg.content, color = msg.author.colour.value)
	emb.set_author(name = msg.author.display_name, icon_url = msg.author.display_avatar.url)
	msg.embeds.insert(0, emb)
	msg.content = None
	return msg
