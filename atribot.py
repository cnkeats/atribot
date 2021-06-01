
import discord
import pandas as pd
import xlsxwriter
import re

client = discord.Client()

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))
	channel = client.get_channel(849156812376637493)
	#print(channel.name)

	rows = []

	count = 0
	posts = await channel.history().flatten()
	posts.reverse()
	for elem in posts:
		if 'twitter' in elem.content:

			tw = re.search("(?P<url>https?://[^\s]+)", elem.content).group("url")
			
			duplicateIndex = -1
			for i, row in enumerate(rows):
				if row['tweet'] == '=HYPERLINK("' + tw + '")':
					duplicateIndex = i

			if duplicateIndex != -1:
				row['duplicate posts'] += 1
			else:
				row = {
					'tweet': '=HYPERLINK("' + tw + '")',
					'author': '-',
					'date': '-',
					'likes' : '-',
					'first poster': elem.author.name + '#' + elem.author.discriminator,
					'discTimestamp' : elem.created_at,
					'duplicate posts': 0
				}
				rows.append(row)


	df = pd.DataFrame.from_dict(rows, orient='columns')
	print (df)
	filepath = 'output.xlsx'
	
	writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
	df.to_excel(writer, index=False, sheet_name='Best Tweets')
	workbook = writer.book
	worksheet = writer.sheets['Best Tweets']
	worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)
	writer.save()



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