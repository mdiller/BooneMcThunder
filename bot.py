import conversator as conv
import disnake
from disnake.ext import commands
import json

with open("config_dev.json", "r") as f:
	config = json.loads(f.read())

config_bot_token = config["bot_token"]
config_api_key = config["api_key"]
config_guild_ids = config["guild_ids"]
config_channel_ids = config["channel_ids"]
config_first_message_role = config.get("first_message_role")


intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(
	test_guilds=config_guild_ids,
	intents=intents)

conversator = conv.Conversator(config_api_key, bot.loop)

conversator.input_system("Talk in a hillbilly accent and respond to all messages in a single sentance")
conversator.input_system("Be very witty and clever in your responses")
conversator.input_system("Be very rude to everyone")

first_message_role = None

if config_first_message_role:
	first_message_role = config_first_message_role

first_message = "Ya'll are dumber than a box of rocks"

first_run=True

@bot.event
async def on_ready():
	global first_run
	global first_message
	print("running!")
	if first_run:
		name = bot.user.name
		conversator.input_system(f"Your name is '{name}'")
		channel = bot.get_channel(config_channel_ids[0])
		conversator.input_self(first_message)
		if first_message_role:
			first_message = f"<@&{first_message_role}> {first_message}" 
		await channel.send(first_message)
		first_run = False

@bot.event
async def on_message(message: disnake.Message):
	print(message.content)
	if message.channel.id not in config_channel_ids or message.author.id == bot.user.id:
		return
	if message.content.startswith("// ") or message.content.startswith("("):
		return
	conversator.input_user(message.clean_content)
	async with message.channel.typing():
		response = await conversator.get_response()
		await message.channel.send(response)

if __name__ == '__main__':
	bot.run(config_bot_token)

