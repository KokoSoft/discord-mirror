from math import sqrt

# Based on https://github.com/simonLeary42/daad

DISCORD_FG_HEX_TO_4BIT_INDEX = {
	(0x35, 0x37, 0x3D): 30,  # gray
	(0xD2, 0x1C, 0x24): 31,  # red
	(0x73, 0x8A, 0x05): 32,  # green
	(0xA5, 0x77, 0x05): 33,  # yellow
	(0x20, 0x76, 0xC7): 34,  # blue
	(0xC6, 0x1B, 0x6F): 35,  # pink
	(0x25, 0x92, 0x86): 36,  # cyan
	# "FFFFFF": 37,  # white
}

DISCORD_BG_HEX_TO_4BIT_INDEX = {
	"022029": 40,  # firefly dark blue
	"BD3612": 41,  # orange
	"475B62": 42,  # marble blue
	"536870": 43,  # greyish turquoise
	"708285": 44,  # gray
	"595AB7": 45,  # indigo
	"819090": 46,  # light gray
	"FCF4DC": 47,  # white
}

def color_distance(rgb1, rgb2):
	"calculate Euclidean distance between two RGB colors"
	return sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)))

def closest_discord_color(rgb: list[int], text : str):
	hex_to_4bit_index = DISCORD_FG_HEX_TO_4BIT_INDEX
	# light colors tend to become white, so we made all other colors preferred unless the
	# input color is *really* white (RGB all > 200)
	if all(num > 200 for num in rgb):
		color = 37
	else:
		sorted_discord_hex = sorted(
			hex_to_4bit_index.keys(),
			key=lambda discord_rgb: color_distance(discord_rgb, rgb),
		)
		color = hex_to_4bit_index[sorted_discord_hex[0]]
	return f"\x1b[{color}m{text}\x1b[0m"
