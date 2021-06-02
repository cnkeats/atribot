
import discord
from discord.activity import CustomActivity
from discord.errors import HTTPException
import pandas as pd
import urllib.request
from PIL import Image
from io import BytesIO
from urllib.request import urlopen
import datetime
import pytz
import re
import configparser
import sys
import textwrap

def run(config):
    print('running')
    tokenFile = config.get('Atribot', 'bot')
    token = open('config/{0}'.format(tokenFile)).read()

    client.analysisChannelId = config.get('Atribot', 'channel')
    client.admins = [int(i) for i in config.get('Atribot', 'admins').split(', ')]
    client.game = config.get('Atribot', 'game')

    client.config = config
    client.run(token)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name=client.game))

@client.event
async def on_message(message):
    # Never process own messages
    if message.author == client.user:
        return
    
    # Ignore users that aren't Admins
    if message.author.id not in client.admins:
        return

    print('Admin message sent in #{0} - id.{1}'.format(message.channel.name, message.channel.id))
    print('Author was: \t{0}'.format(message.author.name))
    print('Date was: \t{0}'.format(message.created_at))
    print('Content was: \t{0}'.format(message.content))
    print(message.created_at)
    print()

    if message.content == '!kill':
        await message.channel.send('Bye :(')
        sys.exit(1)

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('!export'):
        
        months = [
            'january',
            'february',
            'march',
            'april',
            'may',
            'june',
            'july',
            'august',
            'september',
            'october',
            'november',
            'december'
        ]

        requestedMonths = [index+1 for index, month in enumerate(months) if month in message.content.lower()]
        print('requested {0}'.format(requestedMonths))

        if len(requestedMonths) != 1:
            print('More than one month requested.')
            await message.channel.send('My apologies, but you need to specify exactly one month for an export.')
            return

        month = requestedMonths[0]
        firstOfMonth = datetime.datetime(datetime.datetime.today().year, month, 1)
        firstOfNextMonth = datetime.datetime(firstOfMonth.year, firstOfMonth.month+1, firstOfMonth.day)


        analysisChannel = client.get_channel(int(client.analysisChannelId))
        print('Analysis channel #{0} - id.{1}'.format(analysisChannel.name, client.analysisChannelId))
        await message.channel.send('Analyzing <#{0}>'.format(analysisChannel.id))
        print('Working...')
        await message.channel.send("Working...")

        rows = []
        # TODO: Use history filters instead of weird custom timezone stuff
        posts = await analysisChannel.history(limit=10000, after=firstOfMonth, before=firstOfNextMonth, oldest_first=True).flatten()
        print('I found {0} posts. I am extracting relevant ones now.'.format(len(posts)))
        await message.channel.send('I found {0} posts. I am extracting relevant ones now.'.format(len(posts)))

        for elem in posts:

            if 'twitter' in elem.content:
                embeds = elem.embeds

                tw = re.search("(?P<url>https?://[^\s]+)", elem.content).group("url")

                duplicateIndex = -1
                for i, row in enumerate(rows):
                    if row['link'] == tw:
                        duplicateIndex = i

                if duplicateIndex != -1:
                    row['duplicates'] += 1
                else:
                    if len(embeds) > 0:
                        likes = -1
                        retweets = -1
                        embeded_images = ''
                        if len(embeds) > 0 and len(embeds[0].image) > 0:
                            #print('text: ' + elem.embeds[0].description)
                            embeded_images = [embed.image.url for embed in embeds]
                            #print('images: ' + str(embeded_images))

                            # TODO: Replace with Twitter API instead of using Embeds
                            for embed in embeds:
                                if len(embed.fields) > 0:
                                    for field in embed.fields:
                                        if field.name == 'Likes':
                                            likes = field.value
                                        elif field.name == 'Retweets':
                                            retweets = field.value

                        #else:
                            #print('text: ' + elem.embeds[0].description)
                        #print('')

                        row = {
                            'link': tw,
                            'text content': elem.embeds[0].description,
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

        filepath = 'output/best_tweets_' + months[firstOfMonth.month-1] + '.xlsx'
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Best Tweets')
        workbook = writer.book
        worksheet = writer.sheets['Best Tweets']

        print(df)

        if (df.shape[1] > 0):
            worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)

            format = workbook.add_format()
            format.set_align('center')
            format.set_align('vcenter')
            format.set_text_wrap(True)

            linkFormat = workbook.get_default_url_format()
            linkFormat.set_align('center')
            linkFormat.set_align('vcenter')


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
                        print('There was an issue processing image data for {0} - {1}'.format(url, e))

            worksheet.set_column(0, 0, 438/7, format)
            worksheet.set_column(1, 1, 372/7, format)
            worksheet.set_column(2, 2, 125/7, format)
            worksheet.set_column(3, 4, 50/7, format)
            worksheet.set_column(5, 6, 75/7, format)
            worksheet.set_column(7, 7, 120/7, format)
            worksheet.set_column(8, 8, 133/7, format)
            worksheet.set_column(9, 9, 100/7, format)

            writer.save()

            try:
                await message.channel.send("Here is your data! I found {0} unique tweets.".format(df.shape[0]), file=discord.File(filepath))
            except HTTPException as e:
                await message.channel.send("The spreadsheet was too big to upload to this channel! Contact <@169651896359976961> for help!")
        else:
            await message.channel.send("That's weird. There were no tweets posted for that month... :thinking:")

        print('done processing tweets')
    print()
