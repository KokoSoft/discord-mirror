import copy
from parsers import *
import re
import discord as discord_bot

class ModLogParser:
	def __init__(self,
		file_name : str = None,		# Dump entries to specified file
	):
		self.file = open(file_name, 'at', encoding='utf-8') if file_name else None
		self.users = {}
		super().__init__()

	def set_bot(self, bot : discord_bot.Client):
		self.bot = bot

	@staticmethod
	def get_value(embed, name):
		if isinstance(name, str):
			name = [ name.casefold() ]
		else:
			name = [ n.casefold() for n in name ]

		v = next((sub for sub in embed.get('fields', []) if sub.get('name', '').casefold() in name), None)
		return v.get('value', '') if v else ''

	@staticmethod
	def clean_up(field):
		return not field['name'].casefold() in [
			'Streak'.casefold(),
			'Seria'.casefold(),
			'Reduction Option'.casefold(),
			'Możliwość skrócenia kary'.casefold()
		]

	async def get_user(self, str):
		m = re.findall(r'\<@([0-9]+)>', str)
		if not m:
			return None

		user_id = int(m[0])
		if user_id in self.users:
			return self.users[user_id]

		user = self.bot.get_user(user_id)
		if not user:
			try:
				user = await self.bot.fetch_user(user_id)
			except:
				return None
	
		if not user:
			return None

		result = {
			'id': user.id,
			'name': user.name,
			'display_name': user.display_name,
			'global_name': user.global_name,
			'public_flags': user.public_flags.value,
			'display_avatar': user.display_avatar.url,
			'created_at': user.created_at.timestamp()
		}

		if user.accent_color:
			result['accent_color'] = user.accent_color.value

		if user.banner:
			result['banner'] = user.banner.url

		if user.avatar_decoration:
			result['avatar_decoration'] = user.avatar_decoration.url

		self.users[user_id] = result
		return result

	# Get user and moderator profile
	async def parse_embed(self, embed_obj : discord_bot.Embed):
		emb = embed_obj.to_dict()
		user_str = emb.get('description', self.get_value(emb, 'Użytkownik'))
		emb['user'] = user = await self.get_user(user_str)
		emb['mod'] = mod = await self.get_user(self.get_value(emb, ['Moderator', 'Mod']))

		# Some embeds can have no fiels, eq. video
		if 'fields' in emb:
			reason = self.get_value(emb, ['Reason', 'Powód'])
			emb['fields'] = list(filter(self.clean_up, emb['fields']))
			user_name = user.get('display_name') if user else emb.get('author', {}).get('name')
			mod_name = mod.get('display_name') if mod else None
			timestamp = emb.get('timestamp', 'Uknown')
			timestamp = timestamp[:19].replace('T',' ')
			print(timestamp, user_name, emb.get('title','').lower(), 'by', mod_name, f"'{reason}'")

		return emb

	# Edit embed layout
	def format_embed(self, embed):
		entry = copy.deepcopy(embed)

		user = entry['user']
		mod = entry['mod']
		idx = int('author' in entry)
		if mod:
			entry['fields'][idx]['inline'] = False
			entry['fields'].insert(idx + 1, {'name' : 'Mod name', 'value': f"`{mod['display_name']}`", 'inline': True})
			entry['fields'].insert(idx + 2, {'name' : 'Mod login', 'value': f"`{mod['name']}`", 'inline': True})
		if user:
			entry['fields'].insert(idx, {'name' : 'User name', 'value': f"`{user['display_name']}`", 'inline': True})
			entry['fields'].insert(idx + 1, {'name' : 'User login', 'value': f"`{user['name']}`", 'inline': True})

		emb = discord_bot.Embed.from_dict(entry)
		if user:
			emb.set_author(
				name = f"{user['display_name']} (login: {user['name']})",
				icon_url = user['display_avatar'])
		return emb

	async def __call__(self, client, message):
		cnt = 0
		for msg in preserve_author(client, message, True):
			yield await self.parse(client, message, msg, cnt)
			cnt += 1

	async def parse(self, client, message, msg, cnt):
		file_entry = {	'id' : message.id,
						'counter' : cnt,
						'author' : {
							'id' : message.author.id,
							'name' : message.author.name
						},
						'content' : message.content }

		if message.content:
			print("mod-log:", message.author.name, message.content)

		embeds = []
		file_embeds = []
		for emb in msg.embeds:
			entry = await self.parse_embed(emb)
			file_embeds.append(entry)
			embeds.append(self.format_embed(entry))
			
		msg.embeds = embeds
		if file_embeds:
			file_entry['embeds'] = file_embeds

		self.write(file_entry)
		return msg

	def write(self, entry):
		if self.file:
			self.file.write(str(entry) + ',\n')

	def __del__(self):
		if self.file:
			self.file.close()
