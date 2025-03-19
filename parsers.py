from forwarder import ParsedMessage
import discord_self.discord as discord_user
import discord as discord_bot
too_big = False
have_dejw = 0

async def get_referenced_message(client : discord_user.Client,
						   reference : discord_user.MessageReference):
	if reference.cached_message:
		return reference.cached_message

	channel = client.get_channel(reference.channel_id)
	try:
		return await channel.fetch_message(reference.message_id)
	except discord_user.errors.NotFound:
		return None

async def preserve_author(client, message):
	global too_big
	global have_dejw
	#for m in message.mentions:
	#		# Zawołani użytkownicy i ci na których wiadomośc odpowiedziano, global_name nie istnieje
	#		print('mentions', m.name, m.display_name, m.id)

	#for m in message.role_mentions:
	#	print('role_mentions', m.name, m.id)
	#
	#for m in message.channel_mentions:
	#	print('channel_mentions', m.name, m.id)
	#if have_dejw > 3:
	#	return None

	msg = ParsedMessage(message)
	if len(msg.content) > 2000:
		print('Content too long!')
		return None

	for f in msg.attachments:
		if f.size >= 8*1024*1024:
			too_big = True
			break

	dejw = msg.username == 'dejw'
	#if too_big and dejw:
	#	have_dejw += 1

	#if not too_big or not dejw:
	#	return None

	#if msg.content:
	msg.content = f"**{message.author.display_name}**: {msg.content}"
	msg.username = f'{msg.username} as {message.author.display_name}'
	if len(msg.content) > 2000:
		msg.content = content

	print(f"Message ch: {message.channel.id} id: {message.id}, name: {message.author.name}, dispaly: {message.author.display_name}")
	for snap in message.message_snapshots:
		snp = ParsedMessage(snap)


		print(f'Snap {snap.content}')
		for e in snap.embeds:
			print(f'Snap embed {e}')
		for a in snap.attachments:
			print(f'Snap attach {a}')
			


	#print(message.content, message.clean_content, message.embeds, message.attachments, message.type, message.reference)
	# MessageType.reply
	if False and message.reference and message.type == discord_user.MessageType.default:
		print(f"Reference ch: {message.reference.channel_id} id: {message.reference.message_id}")
		m = await get_referenced_message(client, message.reference)
		if m:
			print('	ref msg:', m, m.author, m.author.name, m.author.display_name)
		else:
			print('	MISSING REF MESSAGE');
	return None
	return msg

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
