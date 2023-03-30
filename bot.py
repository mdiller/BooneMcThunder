import conversator as conv
import disnake
from disnake.ext import commands
import json
import re
import openai
import aiohttp
from io import BytesIO
import functools
from concurrent.futures import ThreadPoolExecutor

with open("config_dev.json", "r") as f:
	config = json.loads(f.read())

config_bot_token = config["bot_token"]
config_api_key = config["api_key"]
config_guild_ids = config["guild_ids"]
config_channel_ids = config["channel_ids"]

openai.api_key = config_api_key

intents = disnake.Intents.default()
intents.message_content = True

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_guild_commands = True

bot = commands.Bot(
	command_sync_flags=command_sync_flags,
	test_guilds=config_guild_ids,
	intents=intents)

conversator = conv.Conversator(bot.loop)

first_message = None
first_message_regex = "START: (.*)\n"

prompt_text = ""
prompt_file = config.get("prompt")
if prompt_file:
	with open(prompt_file, "r") as f:
		prompt_text = f.read()
	match_start = re.search(first_message_regex, prompt_text)
	if match_start:
		first_message = match_start.group(1)
		prompt_text = re.sub(first_message_regex, "", prompt_text)
	conversator.input_system(prompt_text)
	print(f"loaded: {prompt_file}")
	print(prompt_text)

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
		await message.channel.send(response)

def request_image(prompt: str):
	response = openai.Image.create(
		prompt=prompt,
		n=1,
		size="1024x1024"
	)
	return response["data"][0]["url"]

@bot.slash_command(description="draws an image")
async def draw(inter: disnake.CmdInter, prompt: str):
	await inter.response.defer()

	image_url = await bot.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(request_image, prompt))

	http_session = aiohttp.ClientSession(loop=bot.loop)
	async with http_session.get(image_url) as r:
		if r.status == 200:
			bytes = BytesIO(await r.read())
			await inter.send(file=disnake.File(bytes, filename="result.png"))
		else:
			await inter.send(f"Oops something broke. Error code: {r.status}")

@bot.message_command(description="disagrees with the message")
async def disagree(inter: disnake.CmdInter, message: disnake.Message):
	await inter.response.defer()
	convo = conv.Conversator(bot.loop)
	convo.input_system(prompt_text)
	convo.input_user(message.clean_content)
	convo.input_system("Disagree with the above message. Be descriptive and prove why they are wrong")
	response = await convo.get_response()
	response = f"{message.author.mention} {response}"
	await inter.send(response)

if __name__ == '__main__':
	bot.run(config_bot_token)

