markov chain twitter bot, reads a twitter archive and generates new tweets from that

## Requirements

Install python package requirements with

```
$ pip install -r requirements.txt
```

## Setup

1. At first login to your twitter account and go to https://twitter.com/settings/account
2. Request your twitter archive and wait for the mail that it is complete
3. Download the twitter archive zip file
4. Import the archive file by calling `python nitoahc.py --import /path/to/archive.zip`

Now you can generate new tweets by calling `python nitoahc.py --print`

## Twitter setup

1. Create a new twitter app at https://apps.twitter.com
2. Make sure you allow the app to post
3. Get your keys from the "Keys and Access Tokens" tab (you need "Consumer Key (API Key)" and "Consumer Secret (API Secret)")
4. Fetch oauth tokens:

```
$ python nitoahc.py --twitter-key <key> --twitter-secret <secret> --auth
Please visit:
https://api.twitter.com/oauth/authenticate?oauth_token=xxx

And restart this script with --pin <Pin> after authenticating.
$ python nitoahc.py --pin <pin>
```

Now send a tweet by calling `python nitoahc.py --tweet`
