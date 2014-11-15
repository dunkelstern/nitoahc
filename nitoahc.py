#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twython import Twython, TwythonError
from zipfile import ZipFile
from pymarkovchain import MarkovChain
from sys import exit
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
from datetime import datetime
from calendar import timegm

import random
import argparse
import os
import json
import re

# set output to utf-8
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
random.seed(timegm(datetime.now().utctimetuple()))

parser = argparse.ArgumentParser(description='Tweet markov chain generated nonsense to an account.')

# config file
parser.add_argument('--config', dest='config', default=os.path.expanduser('~/.nitoahc_rc'), help='Configuration file to use (default: ~/.nitoahc_rc)')
parser.add_argument('--db', dest='db', help='Markov DB to use (default: ~/.nitoahc_db)')
parser.add_argument('--twitter-key', dest='app_key', help='Twitter App key')
parser.add_argument('--twitter-secret', dest='app_secret', help='Twitter App secret')

# twitter
parser.add_argument('--auth', dest='auth', action='store_const', const=True, help='delete twitter auth tokens and start over')
parser.add_argument('--pin', dest='pin', help='save pin from twitter auth')

# archive import
parser.add_argument('--reset-corpus', action='store_const', const=True, dest='reset', help='reset markov corpus')
parser.add_argument('--import', dest='import_archive', help='import twitter archive as markov corpus (adds to corpus)')

# tweet generation
parser.add_argument('--print', action='store_const', const=True, dest='print_tweet', help='print a tweet')
parser.add_argument('--tweet', action='store_const', const=True, dest='tweet', help='send a tweet')

args = parser.parse_args()

def load_config(filename):
	global DB_FILE, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
	config = SafeConfigParser()
	config.read(filename)
	try:
		DB_FILE = config.get('markov', 'db_file')
	except (NoOptionError, NoSectionError):
		DB_FILE = None

	try:
		try:
			APP_KEY    = config.get('twitter', 'app_key')
			APP_SECRET = config.get('twitter', 'app_secret')
		except NoOptionError:
			APP_KEY = None
			APP_SECRET = None
		try:
			OAUTH_TOKEN    = config.get('twitter', 'oauth_token')
			OAUTH_TOKEN_SECRET = config.get('twitter', 'oauth_secret')
		except NoOptionError:
			OAUTH_TOKEN = None
			OAUTH_TOKEN_SECRET = None
	except NoSectionError:
		APP_KEY = None
		APP_SECRET = None
		OAUTH_TOKEN = None
		OAUTH_TOKEN_SECRET = None


def save_config(filename):
	config = SafeConfigParser()
	config.add_section('twitter')
	config.set('twitter', 'app_key', APP_KEY if APP_KEY else "")
	config.set('twitter', 'app_secret', APP_SECRET if APP_SECRET else "")
	if OAUTH_TOKEN != None:
		config.set('twitter', 'oauth_token', OAUTH_TOKEN)
	if OAUTH_TOKEN_SECRET != None:
		config.set('twitter', 'oauth_secret', OAUTH_TOKEN_SECRET)
	
	if DB_FILE:
		config.add_section('markov')
		config.set('markov',  'db_file', DB_FILE)
	with open(filename, 'w') as f:
		config.write(f)

def import_archive(filename, markov):
	rt_regex      = re.compile(r'RT ')
	reply_regex   = re.compile(r'@[^ ]*')
	hashtag_regex = re.compile(r'#[^ ]*')
	link_regex    = re.compile(r'http[s]*://[^ ]*')

	action_regex  = re.compile(r'\*(.+)\*')
	parens_regex  = re.compile(r'\((.+)\)')

	corpus = ""
	with ZipFile(filename, "r") as zip:
		files = zip.namelist()
		tweet_files = []
		for file in files:
			if 'data/js/tweets' in file:
				tweet_files.append(file)
		for file in tweet_files:
			data = zip.read(file)
			data = data[data.find('\n')+1:]
			parsed = json.loads(data)
			for tweet in parsed:
				text = tweet['text']
				repl = []
				repl.extend(rt_regex.findall(text))
				repl.extend(reply_regex.findall(text))
				repl.extend(hashtag_regex.findall(text))
				repl.extend(link_regex.findall(text))
				for r in repl:
					text = text.replace(r, '')

				result = action_regex.search(text)
				if result:
					text = text.replace(text[result.start():result.end()], result.group(1))

				result = parens_regex.search(text)
				if result:
					text = text.replace(text[result.start():result.end()], result.group(1))

				text = text.replace('&lt;', '<')
				text = text.replace('&gt;', '>')
				text = text.replace('&amp;', '&')
				text = text.replace(u' - ', ' ')
				text = text.replace(u'"', '')
				text = text.replace(u'“', '')
				text = text.replace(u'”', '')
				text = text.replace(u'„', '')
				text = text.replace(u'‟', '')
				text = text.replace("\n", ' ')
				text = text.strip()
				corpus = corpus + ". " + text
	markov.generateDatabase(corpus)
	markov.dumpdb()

def make_tweet(markov):
	tweet = markov.generateString()
	while len(tweet) > 140 or len(tweet) < 42:
		tweet = markov.generateString()
	return tweet

OAUTH_TOKEN = None
OAUTH_TOKEN_SECRET = None

CONFIG_FILE = args.config
load_config(CONFIG_FILE)
resave_config = False

DB_FILE = os.path.expanduser("~/.nitoahc_db")
if args.db != None:
	resave_config = True
	DB_FILE = args.db

if args.app_key != None:
	resave_config = True
	APP_KEY = args.app_key
if args.app_secret != None:
	resave_config = True
	APP_SECRET = args.app_secret

if args.auth == True:
	resave_config = True
	OAUTH_TOKEN = None
	OAUTH_TOKEN_SECRET = None

if resave_config:
	save_config(CONFIG_FILE)

if args.auth == True:
	twitter = Twython(APP_KEY, APP_SECRET)
	auth = twitter.get_authentication_tokens()

	OAUTH_TOKEN = auth['oauth_token']
	OAUTH_TOKEN_SECRET = auth['oauth_token_secret']
	save_config(CONFIG_FILE)

	print "Please visit:"
	print auth['auth_url']
	print
	print "And restart this script with --pin <Pin> after authenticating."
	exit(0)

if args.pin != None:
	twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	try:
		final_step = twitter.get_authorized_tokens(args.pin)
	except TwythonError as e:
		print e
		exit(1)

	OAUTH_TOKEN = final_step['oauth_token']
	OAUTH_TOKEN_SECRET = final_step['oauth_token_secret']
	save_config(CONFIG_FILE)

	print "Application authorized!"
	exit(0)

if args.reset == True:
	os.remove(DB_FILE)
	print "DB-File removed"
	exit(0)

markov = MarkovChain(DB_FILE)

if args.import_archive != None:
	import_archive(args.import_archive, markov)
	print "File imported"
	exit(0)

if args.print_tweet == True:
	print make_tweet(markov)
	exit(0)

if args.tweet == True:
	twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	text = make_tweet(markov)
	twitter.update_status(status=text)
	print "Tweet sent"
	exit(0)
