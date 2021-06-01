
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
	posts = await channel.history().flatten()
	posts.reverse()
	for elem in posts:
		if 'twitter' in elem.content:

			embeds = elem.embeds

			tw = re.search("(?P<url>https?://[^\s]+)", elem.content).group("url")
			
			duplicateIndex = -1
			for i, row in enumerate(rows):
				if row['link'] == '=HYPERLINK("' + tw + '")':
					duplicateIndex = i

			if duplicateIndex != -1:
				row['duplicate posts'] += 1
			else:
				likes = '?'
				retweets = '?'
				embeded_images = ''
				if len(embeds[0].image) > 0:
					print('text: ' + elem.embeds[0].description)
					embeded_images = [embed.image.url for embed in embeds]
					print('images: ' + str(embeded_images))

					for embed in embeds:
						if len(embed.fields) > 0:
							for field in embed.fields:
								if field.name == 'Likes':
									likes = field.value
									print('there are this many likes: ' + str(likes))
								elif field.name == 'Retweets':
									retweets = field.value
						
				else:
					print('text: ' + elem.embeds[0].description)
				print('')

				row = {
					'link': '=HYPERLINK("' + tw + '")',
					'text content': elem.embeds[0].description[0:50] + ' ...',
					#'image content': embeded_images,
					'author': '-',
					'date': '-',
					'likes' : likes,
					'retweets' : retweets,
					'first poster': elem.author.name + '#' + elem.author.discriminator,
					'discTimestamp' : elem.created_at,
					'duplicate posts': 0
				}
				rows.append(row)


	df = pd.DataFrame.from_dict(rows, orient='columns')
	print (df)

	filepath = 'output.xlsx'
	writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
	df.to_excel(writer, index=False, sheet_name='Best Tweets')
	worksheet = writer.sheets['Best Tweets']
	worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)

	writer.save()

@client.event
async def on_message(message):
	channel = message.channel
	if message.author == client.user:
		return
	
	# Ignore users that aren't Krohnos (for now)
	if message.author != 169651896359976961:
		return

	if message.content.startswith('!sleep'):
		bot.toggleSleep()
		await message.channel.send('sleeping: %s' % bot.sleeping)
		return

	if bot.sleeping:
		return

	if message.content.startswith('$hello'):
		await message.channel.send('Hello!')
	
	if message.content.startswith('!export'):

		rows = []
		posts = await channel.history().flatten()
		posts.reverse()
		for elem in posts:
			if 'twitter' in elem.content:

				embeds = elem.embeds

				tw = re.search("(?P<url>https?://[^\s]+)", elem.content).group("url")
				
				duplicateIndex = -1
				for i, row in enumerate(rows):
					if row['link'] == '=HYPERLINK("' + tw + '")':
						duplicateIndex = i

				if duplicateIndex != -1:
					row['duplicate posts'] += 1
				else:
					likes = '?'
					retweets = '?'
					embeded_images = ''
					if len(embeds[0].image) > 0:
						print('text: ' + elem.embeds[0].description)
						embeded_images = [embed.image.url for embed in embeds]
						print('images: ' + str(embeded_images))

						for embed in embeds:
							if len(embed.fields) > 0:
								for field in embed.fields:
									if field.name == 'Likes':
										likes = field.value
										print('there are this many likes: ' + str(likes))
									elif field.name == 'Retweets':
										retweets = field.value
							
					else:
						print('text: ' + elem.embeds[0].description)
					print('')

					row = {
						'link': '=HYPERLINK("' + tw + '")',
						'text content': elem.embeds[0].description[0:50] + ' ...',
						#'image content': embeded_images,
						'author': '-',
						'date': '-',
						'likes' : likes,
						'retweets' : retweets,
						'first poster': elem.author.name + '#' + elem.author.discriminator,
						'discTimestamp' : elem.created_at,
						'duplicate posts': 0
					}
					rows.append(row)


		df = pd.DataFrame.from_dict(rows, orient='columns')
		print (df)

		filepath = 'output.xlsx'
		writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
		df.to_excel(writer, index=False, sheet_name='Best Tweets')
		worksheet = writer.sheets['Best Tweets']
		worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)

		writer.save()

		await message.channel.send(file=discord.File('output.xlsx'))

class Bot(object):
	def __init__(self):
		self.sleeping = False

	def toggleSleep(self):
		self.sleeping = not self.sleeping

bot = Bot()

print('\n\n\n\n\n\n\n\n')

tokenFile = open('config\sandbag.token')
token = tokenFile.read()

client.run(token)