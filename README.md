twittercorp
===========

Make a regionally aware Twitter corpus.

The Python script does not rely on the geocoding of the tweets, but rather on the reported location of the twitter user.

How to proceed:

0) make sure you have the dependencies for this script: python-twitter 1.0 (https://code.google.com/p/python-twitter/) and geopy 0.95.1 (https://code.google.com/p/geopy/).

1) apply for a Twitter API key via https://dev.twitter.com/apps/new and enter it in tw.py

2) make a list of the locations that you want to scrape, and put them (one location per line) in cities.txt

3) provide tw.py with a number of initial seeds (like newspapers or politicians) that reveal their location. (via settings.txt)

4) check the other fields that you need to fill in in settings.txt

Just run tw.py for some time and the corpus will grow. If something goes wrong, just start it again and the script should pick up where it ended.
