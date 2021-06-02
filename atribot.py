
import discord
from discord.activity import CustomActivity
import pandas as pd
import urllib.request
from PIL import Image
from io import BytesIO
from urllib.request import urlopen
import datetime
import pytz
import re

client = discord.Client()

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))
	channel = client.get_channel(849156812376637493)
	await client.change_presence(activity=discord.Game(name="with your heart <3"))

@client.event
async def on_message(message):
	channel = message.channel
	if message.author == client.user:
		return

	# Ignore users that aren't Krohnos (for now)
	if message.author.id != 169651896359976961:
		return

	if message.content.startswith('!hello'):
		await message.channel.send('Hello!')

	if message.content.startswith('!export'):
		analysisChannel = client.get_channel(799195020808552478)
		print('Working...')
		await message.channel.send("Working...")

		rows = []
		# TODO: Use history filters instead of weird custom timezone stuff
		posts = await analysisChannel.history(limit=10000).flatten()
		print('got history')
		posts.reverse()
		for elem in posts:
			if 'twitter' in elem.content:

				pacific = pytz.timezone('US/Pacific')
				today = datetime.datetime.today()
				first = today.replace(day=1)
				lastMonth = datetime.datetime(datetime.date.today().year, first.month-1, 1)
				first = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

				if elem.created_at.astimezone(pacific) > lastMonth.astimezone(pacific) and elem.created_at.astimezone(pacific) < first.astimezone(pacific):

					embeds = elem.embeds

					tw = re.search("(?P<url>https?://[^\s]+)", elem.content).group("url")

					duplicateIndex = -1
					for i, row in enumerate(rows):
						if row['link'] == '=HYPERLINK("' + tw + '")':
							duplicateIndex = i

					if duplicateIndex != -1:
						row['duplicates'] += 1
					else:
						if len(embeds) > 0:
							likes = '?'
							retweets = '?'
							embeded_images = ''
							if len(embeds) > 0 and len(embeds[0].image) > 0:
								print('text: ' + elem.embeds[0].description)
								embeded_images = [embed.image.url for embed in embeds]
								print('images: ' + str(embeded_images))

								# TODO: Replace with Twitter API instead of using Embeds
								for embed in embeds:
									if len(embed.fields) > 0:
										for field in embed.fields:
											if field.name == 'Likes':
												likes = field.value
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
								'duplicates': 0
							}
							rows.append(row)


		df = pd.DataFrame.from_dict(rows, orient='columns')
		#print(df)

		filepath = 'output/best_tweets_' + 'jan feb mar apr may jun jul aug sep oct mov dec'.split()[first.month-2] + '.xlsx'
		writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
		df.to_excel(writer, index=False, sheet_name='Best Tweets')
		workbook = writer.book
		worksheet = writer.sheets['Best Tweets']

		if (df.shape[1] > 0):
			worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)

			format = workbook.add_format()
			format.set_align('vcenter')


			for key, item in df['image content'].iteritems():
				if (len(item) > 0):
					url = item[0]
					try:
						image_data = BytesIO(urlopen(url).read())
						

						urllib.request.urlretrieve(url, "temp.png")

						with Image.open("temp.png") as img:
							width_100 = img.width
							height_100 = img.height

						cell_width = 125
						cell_height = 200

						scale_value = cell_width / width_100

						worksheet.set_row(key+1, (scale_value * height_100 * .75))
						worksheet.write_string('C' + str(key+2), '')
						worksheet.insert_image('C' + str(key+2), url, {'image_data': image_data, 'x_scale' : scale_value, 'y_scale' : scale_value})
					except Exception as e:
						print(e)

			worksheet.set_column(0, 0, 438/7, format)
			worksheet.set_column(1, 1, 372/7, format)
			worksheet.set_column(2, 2, 125/7, format)
			worksheet.set_column(3, 4, 50/7, format)
			worksheet.set_column(5, 6, 75/7, format)
			worksheet.set_column(7, 7, 120/7, format)
			worksheet.set_column(8, 8, 133/7, format)
			worksheet.set_column(9, 9, 100/7, format)

			writer.save()

			await message.channel.send("Here are the posted tweets!", file=discord.File(filepath))
		else:
			await message.channel.send("That's weird. There were no tweets posted last month... :thinking:")

botChoice = open('config/bot_choice.cfg').read()
tokenFile = open('config/' + botChoice.strip())
token = tokenFile.read()

client.run(token)