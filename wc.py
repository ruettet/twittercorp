import re, glob

regex = re.compile(">(.+?)<")
wc = 0
fl = glob.glob("locations/*/*.tweets")
for f in fl:
	fin = open(f, "r")
	xml = fin.read()
	tweets = regex.findall(xml)
	for tweet in tweets:
		wc = wc + len(tweet.split(" "))
	print wc
