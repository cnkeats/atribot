
import discord
from discord.activity import CustomActivity
import pandas as pd
import xlsxwriter
import urllib.request
from PIL import Image
from io import BytesIO
from urllib.request import urlopen
import re

client = discord.Client()

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))
	channel = client.get_channel(849156812376637493)
	#print(channel.name)

	customActivity = CustomActivity("Stealing Quack's job")
	
	await client.change_presence(activity=discord.Game(name="a game"))
	await client.change_presence(activity=discord.Game(name="with your heart <3"))

@client.event
async def on_message(message):
	channel = message.channel
	if message.author == client.user:
		return
	
	# Ignore users that aren't Krohnos (for now)
	if message.author.id != 169651896359976961:
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
										#print('there are this many likes: ' + str(likes))
									elif field.name == 'Retweets':
										retweets = field.value
							
					else:
						print('text: ' + elem.embeds[0].description)
					print('')

					row = {
						'link': '=HYPERLINK("' + tw + '")',
						'text content': elem.embeds[0].description[0:50] + ' ...',
						'image content': embeded_images,
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
		#print(df)

		filepath = 'best_tweets.xlsx'
		writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
		df.to_excel(writer, index=False, sheet_name='Best Tweets')
		workbook = writer.book
		worksheet = writer.sheets['Best Tweets']
		worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)

		format = workbook.add_format()
		format.set_align('vcenter')


		for key, item in df['image content'].iteritems():
			#print(item)
			if (len(item) > 0):
				#print(item[0])

				url = item[0]
				image_data = BytesIO(urlopen(url).read())

				url = url #'https://upload.wikimedia.org/wikipedia/en/thumb/4/43/Ipswich_Town.svg/255px-Ipswich_Town.svg.png'

				urllib.request.urlretrieve(url, "temp.png")

				with Image.open("temp.png") as img:
					width_100 = img.width
					height_100 = img.height
				
				cell_width = 125
				cell_height = 200

				scale_value = cell_width / width_100

				#print('image width: ' + str(img.height))
				#print('image height: ' + str(img.height))
				#print('scale value: ' + str(scale_value))
				#print(scale_value * height_100)

				
				worksheet.set_row(key+1, (scale_value * height_100 * .75))
				worksheet.write_string('C' + str(key+2), '')
				worksheet.insert_image('C' + str(key+2), url, {'image_data': image_data, 'x_scale' : scale_value, 'y_scale' : scale_value})
				
		
		#for i in range(0, 10):
			#worksheet.set_row(i, None, format)
		worksheet.set_column(0, 0, 438/7, format)
		worksheet.set_column(1, 1, 372/7, format)
		worksheet.set_column(2, 2, 125/7, format)
		worksheet.set_column(3, 4, 80/7, format)
		worksheet.set_column(5, 6, 95/7, format)
		worksheet.set_column(7, 7, 120/7, format)
		worksheet.set_column(8, 9, 133/7, format)

		writer.save()

		await message.channel.send("Here is your export!", file=discord.File('best_tweets.xlsx'))

class Bot(object):
	def __init__(self):
		self.sleeping = False

	def toggleSleep(self):
		self.sleeping = not self.sleeping

bot = Bot()

print('\n\n\n\n\n\n\n\n')

tokenFile = open('config/atribot.token')
token = tokenFile.read()

client.run(token)