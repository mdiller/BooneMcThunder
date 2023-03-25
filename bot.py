import conversator as conv
import disnake
from disnake.ext import commands
import json
import re

with open("config.json", "r") as f:
	config = json.loads(f.read())

config_bot_token = config["bot_token"]
config_api_key = config["api_key"]
config_guild_ids = config["guild_ids"]
config_channel_ids = config["channel_ids"]

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(
	test_guilds=config_guild_ids,
	intents=intents)

conversator = conv.Conversator(config_api_key, bot.loop)

first_message = None
first_message_regex = "START: (.*)\n"

prompt_file = config.get("prompt")
if prompt_file:
	with open(prompt_file, "r") as f:
		text = f.read()
	match_start = re.search(first_message_regex, text)
	if match_start:
		first_message = match_start.group(1)
		text = re.sub(first_message_regex, "", text)
	conversator.input_system(text)
	print(f"loaded: {prompt_file}")
	print(text)

first_run = True

@bot.event
async def on_ready():
	global first_run
	global first_message
	print("running!")
	if first_run:
		name = bot.user.name
		conversator.input_system(f"Your name is '{name}'")
		channel = bot.get_channel(config_channel_ids[0])
		if first_message:
			conversator.input_self(first_message)
			await channel.send(first_message)
		first_run = False

@bot.event
async def on_message(message: disnake.Message):
	if message.channel.id not in config_channel_ids or message.author.id == bot.user.id:
		return
	if message.content.startswith("// ") or message.content.startswith("("):
		return
	conversator.input_user(message.clean_content)
	async with message.channel.typing():
		response = await conversator.get_response()
		response = response.lower()
		await message.channel.send(response)

if __name__ == '__main__':
	bot.run(config_bot_token)

