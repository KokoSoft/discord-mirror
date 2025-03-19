from forwarder import ParsedMessage
import discord_self.discord as discord_user

def preserve_author(client, message):
	#for m in message.mentions:
	#		# Zawołani użytkownicy i ci na których wiadomośc odpowiedziano, global_name nie istnieje
	#		print('mentions', m.name, m.display_name, m.id)

	for m in message.role_mentions:
		print('role_mentions', m.name, m.id)

	for m in message.channel_mentions:
		print('channel_mentions', m.name, m.id)

	msg = ParsedMessage(message)
	content = message.clean_content
	if len(content) > 2000:
		return None

	if message.content:
		msg.content = f"**{message.author.display_name}**: {content}"

	if len(msg.content) > 2000:
		msg.content = content

	return msg

def drop_embeds(client, message):
	message.embeds = []
	return message

def delete_parser(client, message):
	msg = ParsedMessage(message)
	content = message.clean_content
	msg.content = f"*From* **{message.channel.name}** *deleted* **{message.author.display_name}** *message*:\n{message.content}"
	return msg

import discord

def as_embed(client, msg):
	emb = discord_bot.Embed(description = msg.content, color = msg.author.colour.value)
	emb.set_author(name = msg.author.display_name, icon_url = msg.author.display_avatar.url)
	msg.embeds.insert(0, emb)
	msg.content = None
	return msg
