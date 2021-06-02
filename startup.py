
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
import bot


def start():
    config = configparser.RawConfigParser()
    configPath = './config/config.cfg'
    config.read(configPath)

    bot.run(config)