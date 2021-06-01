
import discord

client = discord.Client()

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.startswith('!sleep'):
		bot.toggleSleep()
		await message.channel.send('sleeping: %s' % bot.sleeping)
		return

	if bot.sleeping:
		return

	if message.content.startswith('$hello'):
		await message.channel.send('Hello!')


class Bot(object):
	def __init__(self):
		self.sleeping = False

	def toggleSleep(self):
		self.sleeping = not self.sleeping

bot = Bot()


tokenFile = open('config\sandbag.token')
token = tokenFile.read()

client.run(token)