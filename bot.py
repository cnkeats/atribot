
import discord
from discord.activity import CustomActivity
from discord.errors import HTTPException
import pandas as pd
import urllib.request
from PIL import Image
from io import BytesIO
from urllib.request import urlopen
import datetime
import re
import sys
import requests
import json

def run(config):
    print('running')
    tokenFile = config.get('Atribot', 'bot')
    token = open('config/{0}'.format(tokenFile)).read()
    client.twitterToken = open('config/twitter.token').read().strip()

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

        if len(requestedMonths) != 1:
            print('More than one month requested.')
            await message.channel.send('My apologies, but you need to specify exactly one month for an export.')
            return

        month = requestedMonths[0]
        # A hack to get into pacific time - this will break by an hour during daylight savings time
        firstOfMonth = datetime.datetime(datetime.datetime.today().year, month, 1) + datetime.timedelta(hours=8)
        firstOfNextMonth = datetime.datetime(firstOfMonth.year, firstOfMonth.month+1, firstOfMonth.day) + datetime.timedelta(hours=8)


        analysisChannel = client.get_channel(int(client.analysisChannelId))

        if (analysisChannel == None):
            print("I don't have permission to view the requested channel.")
            await message.channel.send("I don't have permission to view the requested channel.")
            return

        print('Analysis channel #{0} - id.{1}'.format(analysisChannel.name, client.analysisChannelId))
        await message.channel.send('Analyzing <#{0}>'.format(analysisChannel.id))
        print('Working...')
        await message.channel.send("Working...")

        rows = []
        # TODO: Use history filters instead of weird custom timezone stuff
        posts = await analysisChannel.history(limit=10000, after=firstOfMonth, before=firstOfNextMonth, oldest_first=True).flatten()
        print('I found {0} posts. I am extracting relevant ones now.'.format(len(posts)))
        await message.channel.send('I found {0} posts. I am extracting relevant ones now.'.format(len(posts)))
        print('Looking for tweets after: {0}'.format(firstOfMonth))

        for elem in posts:

            if tweetURL := re.search('(.*)http(?:s)?:\/\/(?:www\.)?twitter\.com\/([a-zA-Z0-9_]+)/status/([0-9]*).*', elem.content, re.IGNORECASE):
                author = tweetURL.group(2)
                tweet_id = tweetURL.group(3)

                
                url = 'https://api.twitter.com/2/tweets/{0}?tweet.fields=public_metrics,created_at,author_id'.format(tweet_id)
                headers = { 'Authorization' : 'Bearer {0}'.format(client.twitterToken) }
                tweetResponse = requests.get(url, headers=headers)
                tweetData = json.loads(tweetResponse.text)
                print(tweetData)
                return

                url = 'https://api.twitter.com/2/users/{0}?user.fields=verified'.format(tweetData['data']['author_id'])
                authorResponse = requests.get(url, headers=headers)
                authorData = json.loads(authorResponse.text)

                author_handle = authorData['data']['username']
                author_name = authorData['data']['name']
                author_verified = authorData['data']['verified']

                tweet_text = tweetData['data']['text']
                tweet_likes = tweetData['data']['public_metrics']['like_count']
                tweet_retweets = tweetData['data']['public_metrics']['retweet_count']
                tweet_quotes = tweetData['data']['public_metrics']['quote_count']
                tweet_replies = tweetData['data']['public_metrics']['reply_count']
                tweet_date = tweetData['data']['created_at']

                tweetURL = 'https://twitter.com/{0}/status/{1}'.format(author_handle, tweet_id)

                embeds = elem.embeds

                duplicateIndex = -1
                for i, row in enumerate(rows):
                    if row['link'] == tweetURL:
                        duplicateIndex = i

                if duplicateIndex != -1:
                    row['duplicates'] += 1
                else:
                    if len(embeds) > 0:
                        embeded_images = ''
                        if len(embeds) > 0 and len(embeds[0].image) > 0:
                            #print('text: ' + elem.embeds[0].description)
                            embeded_images = [embed.image.url for embed in embeds]
                            #print('images: ' + str(embeded_images))

                        #else:
                            #print('text: ' + elem.embeds[0].description)
                        #print('')

                    row = {
                        'link': tweetURL,
                        'text content': tweet_text,
                        'image content': embeded_images,
                        'author': '{0} (@{1} {2})'.format(author_name, author_handle, '✓' if author_verified else ''),
                        'date': tweet_date,
                        'quotetweets' : tweet_quotes,
                        'replies' : tweet_replies,
                        'first poster': elem.author.name + '#' + elem.author.discriminator,
                        'discTimestamp' : elem.created_at,
                        'duplicates': 0,
                        'likes' : tweet_likes,
                        'retweets' : tweet_retweets
                    }
                    rows.append(row)
                    #print(row)
                    #return

        df = pd.DataFrame.from_dict(rows, orient='columns')

        filepath = 'output/best_tweets_' + months[firstOfMonth.month-1] + '.xlsx'
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Best Tweets')
        workbook = writer.book
        worksheet = writer.sheets['Best Tweets']
        
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
                    worksheet.write_string('C' + str(key+2), '')
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
