import forwarder
import discord
from datetime import datetime, timedelta
import copy
import tokens

# Oryginalna chujnia
# 👑 Informacje
CHANNEL_ID_GEJ_REGULAMIN						= 1120731221085913098	# @ *
CHANNEL_ID_GEJ_OGLOSZENIA						= 1082668156461518868	# @ *
CHANNEL_ID_GEJ_LOBBY							= 1092031369611333662	# @ *
CHANNEL_ID_GEJ_AJEMGE_WEJTING_ROOM				= 1325459814108758087	# @ *
CHANNEL_ID_GEJ_MOD_LOG							= 1327019613715828737	# @
CHANNEL_ID_GEJ_PODSUMOWANIE_STREAMOW			= 1332574550512369757	# @ *

# 🌎 Kanały Tekstowe
CHANNEL_ID_GEJ_KULTURKA							= 1303196845387943977	#   *
CHANNEL_ID_GEJ_MNIEJ_KULTURKI					= 1330124289378095175	#   *
CHANNEL_ID_GEJ_BRAK_KULTURKI					= 1305912677222318082	#   *
CHANNEL_ID_GEJ_KIEDY_KUBA_POJDZIE_SIEDZIEC		= 1305911252240826470	#   *
CHANNEL_ID_GEJ_GIFY_I_SCREENSHOTY				= 1304850303547474062	#   *
CHANNEL_ID_GEJ_GEJSONOWSKIE_ANKIETY				= 1328551898927730780	# @ *
CHANNEL_ID_GEJ_OPINIE_O_TELEGRAMIE				= 1346141158178557962	#   *

# 🎬 Strefa Ajemge1 🟣
CHANNEL_ID_GEJ_SHOTY							= 1117197015072379020	#   *
CHANNEL_ID_GEJ_AJEMGE1_SHOTY					= 1319763910471061545	# @ *
CHANNEL_ID_GEJ_POMYSLY_NA_KONTENT				= 1082787629495500951	#   *
CHANNEL_ID_GEJ_OBIETNICE						= 1120731871739904110	#   *
CHANNEL_ID_GEJ_CO_GEJ_NAPISZE_NA_DC_PO_STREAMIE	= 1316185002484043837	#   *
CHANNEL_ID_GEJ_STOPKI_AKTOREK					= 1346078855953383444	# @ *
CHANNEL_ID_GEJ_KRONIKA_KRAKOW					= 1336827689063157790	# @

# 🐱🐶 Strefa Słodkich Zwierzątek  🦦🦊
CHANNEL_ID_GEJ_SLODKIE_PIESKI					= 1329343790284013578	#   *
CHANNEL_ID_GEJ_SLODKIE_KOTKI					= 1156274626167578677	#   *
CHANNEL_ID_GEJ_SLODKIE_WYDRY					= 1330126476812619877	#   *
CHANNEL_ID_GEJ_SLODKIE_INNE_ZWIERZATKA			= 1338821603894493256	#   *

'''
Ajemge1
stage_voice  1317648013530763411 AJEMGE STREAM
category     1319409330709205134 🌈Administracja
text         1314616221412622386 kubus-slodzius
text         1319016664288985258 podania
voice        1190340595185623100 Rozmowy Z Kubusiem <3
text         1141830181363912734 botkanał
text         1331644931558871100 auto-anty-leaker
text         1328682752920260648 biuro-detektywistyczne-adoratorow-sendeja
text         1331656936663289948 sendej
text         1328685342240538718 archiwum-jzsl
category     1082668333888974938 🌈Moderacja
text         1319409686767997090 kubus-slodzius-mod
text         1326985944179544128 regulamin-moderacyjny
category     1169927742511394857 🌈GigaGeje🌈
text         1172508867347886151 💭︱kulturka-vip
category     1082731989242761266 👑 Informacje
text         1120731221085913098 📜︱regulamin
text         1082668156461518868 📣︱ogłoszenia
text         1092031369611333662 👋︱lobby
text         1325459814108758087 📣︱ajemge-wejting-room
text         1327019613715828737 mod-log
text         1332574550512369757 podsumowanie-streamów
text         1330709381175840900 kronika
category     1343260123992428614 TINDEROWCY
text         1299491147697098973 tinderowcy
text         1345749881335054336 umowione-babeczki
text         1345749918140338270 juz-byly
category     1079122293281787975 🌎 Kanały Tekstowe
text         1303196845387943977 💭︱kulturka
text         1330124289378095175 💭︱mniej-kulturki
text         1305912677222318082 🔞︱brak-kulturki
text         1342986517777350740 🔞︱pokazy-zigiego-nsfw
text         1305911252240826470 💭︱kiedy-kuba-pójdzie-siedzieć
text         1304850303547474062 📽︱gify-i-screenshoty
text         1328551898927730780 gejsonowskie-ankiety
text         1346141158178557962 opinie-o-telegramie
text         1346201474891513878 discordowy-konkurs
text         1337374657384546314 𝓿𝓲𝓿𝓲𝓳𝓮𝓼𝓸𝔀𝓷𝓲𝓪
category     1330152816903196682 🎬 Strefa Ajemge1 🟣
text         1117197015072379020 📹︱shoty
text         1319763910471061545 ajemge1-shoty
text         1082787629495500951 📂︱pomysly-na-kontent
text         1120731871739904110 🤥︱obietnice
text         1316185002484043837 co-gej-napisze-na-dc-po-streamie
text         1346078855953383444 stópki-aktorek
text         1336827689063157790 kronika-kraków
text         1303141333317455892 kronika-wroclaw
text         1317638650087079976 tinder-vs-rzeczywistość
text         1246860294274154618 aktorki-głogów
category     1330126880841662525 🐱🐶 Strefa Słodkich Zwierzątek  🦦🦊
text         1329343790284013578 🐶︱słodkie-pieski
text         1156274626167578677 🐱︱słodkie-kotki
text         1330126476812619877 🦦︱słodkie-wydry
text         1338821603894493256 słodkie-inne-zwierzątka
category     1079122293281787976 🎸 Kanały Głosowe
voice        1303196028144455700 🔊︱21:00 Oglądanie Szkolnej
voice        1303196068812554240 🔊︱23:00 REKRUTACJA NA ADMINISTRATORA DC
voice        1323062790608392232 🔊︱Samotnia PA3L i Sendej
voice        1320219763665928232 🔊︱Zigi-Zabawy
voice        1326462544398778442 🔊︱max 5
voice        1317519059784564837 🔊︱max 10
voice        1325572654668972063 🔊︱Poczekalnia samotni  pa3l i sendej
voice        1305614359904387082 🔊︱AFK
voice        1305616939988680714 MAX 25 TYLKO Z MIKRO
voice        1303195649516241008 🔊︱mangozjeby
voice        1303196089138155540 🔊︱max 2
'''

# Ajemcwel
CHANNEL_ID_CWEL_SHOTY					= 1347014812445708308
CHANNEL_ID_CWEL_CZAT_DLA_NOWYCH			= 1347233420258054207

'''
category     1346952480357089433 Kanały tekstowe
category     1346952480357089434 Kanały głosowe
text         1346993660264317070 stream-info
voice        1346952480357089436 GŁOSOWY
text         1346959527332941834 czat-dla-zweryfikowanych
voice        1346994389142081656 GŁOSOWY
voice        1346994399719985183 GŁOSOWY
voice        1346994411766157334 GŁOSOWY
text         1347233420258054207 czat-dla-nowych
text         1347952759902568538 leak
text         1347014812445708308 shoty
text         1347246915766583337 nsfw-ajemge1
text         1347248258753368094 nsfw-other
text         1346952480357089435 logi
text         1347259178334294057 dla-moderatorów
text         1347262555688800266 regulamin
text         1347266753725726720 zdrajcy
'''
	
# test
CHANNEL_ID_TEST_OGOLNY					= 1348027145037021269
CHANNEL_ID_TEST_KULTURKA				= 1348633457835900999
CHANNEL_ID_TEST_MOD_LOG					= 1348821427951894598

CHANNEL_ID_TEST_KRONIKA_KARKOW			= 1348821438387454052
CHANNEL_ID_TEST_UNCENSORED				= 1348818118897700894
CHANNEL_ID_TEST_SHOTY					= 1348821462034808873
CHANNEL_ID_TEST_AJEMGE1_SHOTY			= 1348821525934903297
CHANNEL_ID_TEST_PODSUMOWANIE_STREAMOW	= 1348821490925043762
CHANNEL_ID_TEST_GIFY_I_SCREENSHOTY		= 1348821502354526333
CHANNEL_ID_TEST_TRASH					= 1348821512911585381
CHANNEL_ID_TEST_TEST9					= 1348821537209192521

def preserve_author(message):
	#for m in message.mentions:
	#		# Zawołani użytkownicy i ci na których wiadomośc odpowiedziano, global_name nie istnieje
	#		print('mentions', m.name, m.display_name, m.id)

	for m in message.role_mentions:
		print('role_mentions', m.name, m.id)

	for m in message.channel_mentions:
		print('channel_mentions', m.name, m.id)

	msg = forwarder.ParsedMessage(message)
	content = message.clean_content
	if len(content) > 2000:
		return None

	if message.content:
		msg.content = f"**{message.author.display_name}**: {content}"

	if len(msg.content) > 2000:
		msg.content = content

	return msg

def drop_embeds(message):
	message.embeds = []
	return message

def delete_parser(message):
	msg = forwarder.ParsedMessage(message)
	msg.content = f"*From* **{message.channel.name}** *deleted* **{message.author.display_name}** *message*:\n{message.content}"
	return msg

def as_embed(msg):
	emb = discord.Embed(description = msg.content, color = msg.author.colour.value)
	emb.set_author(name = msg.author.display_name, icon_url = msg.author.display_avatar.url)
	msg.embeds.insert(0, emb)
	msg.content = None
	return msg


import re

class ModLogParser:
	def __init__(self, file_name):
		self.file = open(file_name, 'at', encoding='utf-8')
		self.users = {}

	@staticmethod
	def get_value(embed, name):
		v = next((sub for sub in embed['fields'] if sub['name'] == name), None)
		return v['value'] if v is not None else ''

	@staticmethod
	def clean_up(field):
		return not field['name'] in ['Streak', 'Reduction Option']

	async def get_user(self, str):
		m = re.findall(r'\(([0-9]+)\)', str)
		if not m:
			return None

		user_id = int(m[0])
		if user_id in self.users:
			return self.users[user_id]

		user = bot.get_user(user_id)
		if not user:
			try:
				user = await bot.fetch_user(user_id)
			except:
				return None
	
		if user:
			user = {
				'id': user.id,
				'name': user.name,
				'display_name': user.display_name,
				'global_name': user.global_name,
			}
			self.users[user_id] = user
		return user

	async def __call__(self, message):
		msg = preserve_author(message)

		file_entry = {	'id' : message.id,
						'author' : {
							'id' : message.author.id,
							'name' : message.author.name
						},
						'content' : message.content }

		if message.content:
			print(message.author.name, message.content)

		if message.embeds:
			file_entry['embeds'] = []

		embeds = []
		for emb in msg.embeds:
			user = await self.get_user(emb.description)
			mod = None
			ed = emb.to_dict()
			# Some embeds can have no fiels, eq. video
			if 'fields' in ed:
				ed['fields'] = list(filter(self.clean_up, ed['fields']))
				mod = await self.get_user(self.get_value(ed, 'Moderator'))
				print(emb.timestamp, user['display_name'], emb.title, 'by', mod['display_name'], f"'{self.get_value(ed, 'Reason')}'")

			ed['mod'] = mod
			ed['user'] = user
			file_entry['embeds'].append(copy.deepcopy(ed))

			if mod:
				ed['fields'][0]['inline'] = False
				ed['fields'].insert(1, {'name' : 'Mod name', 'value': f"`{mod['display_name']}`", 'inline': True})
				ed['fields'].insert(2, {'name' : 'Mod login', 'value': f"`{mod['name']}`", 'inline': True})
			if user:
				ed['fields'].insert(0, {'name' : 'User name', 'value': f"`{user['display_name']}`", 'inline': True})
				ed['fields'].insert(1, {'name' : 'User login', 'value': f"`{user['name']}`", 'inline': True})

			embeds.append(emb.from_dict(ed))

		msg.embeds = embeds

		self.file.write(str(file_entry) + ',\n')

		return msg

	def __del__(self):
		if self.file:
			self.file.close()
	
mod_parser = ModLogParser('mod.log')

sources = [
	forwarder.Client(tokens.G, [	# *
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_GIFY_I_SCREENSHOTY,
			destinations = CHANNEL_ID_TEST_GIFY_I_SCREENSHOTY,
			parser = drop_embeds,
			copy_history = True,
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_SHOTY,
			destinations = CHANNEL_ID_TEST_SHOTY,
			parser = drop_embeds,
			copy_history = True,
		),
		forwarder.Config(
			destinations = CHANNEL_ID_TEST_UNCENSORED,
			parser = delete_parser,
			only_deleted = True
		),
	], section_name = "regular", debug = False, presence = discord.Status.invisible),
	forwarder.Client(tokens.K, [	# @
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_PODSUMOWANIE_STREAMOW,
			destinations = CHANNEL_ID_TEST_PODSUMOWANIE_STREAMOW,
			copy_history = True,
			parser = preserve_author,
		),
		forwarder.Config(
			sources = CHANNEL_ID_GEJ_AJEMGE1_SHOTY,
			destinations = CHANNEL_ID_TEST_AJEMGE1_SHOTY,
			parser = drop_embeds,
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

bot = forwarder.Bot(tokens.BOT,
	allowed_mentions = discord.AllowedMentions(users=False, roles=False),
	debug = False,
	list_channels = False)
forwarder.BotRunner(bot, sources).run()
