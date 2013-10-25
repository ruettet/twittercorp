import re, twitter, glob, random, time, codecs, hashlib
from geopy import geocoders
from collections import Counter

def getSettings():
  """ method to read in the settings from settings.txt """
  out = {}
  fin = open("settings.txt", "r")
  txt = fin.read()
  fin.close()
  regex = re.compile("convergence=(\d+)")
  out["convergence"] = int(regex.findall(txt)[0])
  regex = re.compile("locmin=(\d+)")
  out["locmin"] = int(regex.findall(txt)[0])
  regex = re.compile("new_seeds=(.+)")
  out["seeds"] = regex.findall(txt)[0].split(",")
  regex = re.compile("consumer_key=(.+)")
  ckey = regex.findall(txt)[0]
  regex = re.compile("consumer_secret=(.+)")
  csecret = regex.findall(txt)[0]
  regex = re.compile("access_token_key=(.+)")
  atkey = regex.findall(txt)[0]
  regex = re.compile("access_token_secret=(.+)")
  atsecret = regex.findall(txt)[0]
  out["api"] = (ckey, csecret, atkey, atsecret)
  return out

def getPriorSeeds(f):
  """ go through the seedlist and structure them as they should """
  out = []
  try:
    fin = codecs.open(f, "r", "utf-8")
    seeds = fin.readlines()
    fin.close()
    if len(seeds) == 0:
      raise IOError
    for seed in seeds:
      uname = unicode(seed.split(",")[0])
      loc = unicode(",".join(seed.strip().split(",")[1:]))
      if loc != False:
        out.append( (uname, loc) )
  except IOError:
    stts = getSettings()
    seeds = stts["seeds"]
    i = 0
    haveLocs = usersByLoc(seeds)
    while i < len(seeds):
      loc = acceptableLocation(seeds[i+1], [], haveLocs)
      if loc != False:
        seed = (unicode(seeds[i]), unicode(loc[0]))
        out.append(seed)
      i = i + 2
  return out

def getNewSeeds(sample, seeds, api):
  """ wrapper to get from a list of seeds (sample) new seeds that do not occur
      in the given seeds (seeds) already """
  out = []
  i = 1
  for s in sample:
    print "seed ", i, s
    i = i + 1
    friends = getFriends(s, seeds, api)
    remaining = set(friends) - set(seeds) - set(out)
    out.extend(list(remaining))
  return out

def getFriends(s, seeds, api):
  """ call the twitter api for new friends from a single user """
  out = []
  uname = unicode(s[0])
  print "searching friends for", s

  # call to api
  rls = api.GetRateLimitStatus()
  if rls["resources"]["friends"]["/friends/ids"]["remaining"] > 1:
    ids = api.GetFriendIDs(screen_name=uname)
  else:
    sleeptime = rls["resources"]["friends"]["/friends/ids"]["reset"] - time.time()
    print "sleeping for", sleeptime + 5, "seconds"
    time.sleep(sleeptime + 5)
    ids = api.GetFriendIDs(screen_name=uname)

  haveLocs = usersByLoc(seeds)
  count = 1
  for ajd in ids:

    # call to api
    rls = api.GetRateLimitStatus()
    if rls["resources"]["users"]["/users/show/:id"]["remaining"] > 1:
      friend = api.GetUser(user_id=ajd)
    else:
      sleeptime = rls["resources"]["users"]["/users/show/:id"]["reset"] - time.time()
      print "sleeping for", sleeptime + 5, "seconds"
      time.sleep(sleeptime + 5)
      friend = api.GetUser(user_id=ajd)

    floc = unicode(friend.location)
    checkedloc = acceptableLocation(floc, seeds, haveLocs)
    if checkedloc != False:
      print "\tadding:", unicode(friend.screen_name), floc, checkedloc, count, "of", len(ids)
      out.append( (unicode(friend.screen_name), unicode(checkedloc[0])) )
    count = count + 1
  return out

def getLocDB():
  """ read the db in which normalizations of reported locations are stored """
  db = {}
  try:
    fin = codecs.open("locdb.txt", "r", "utf-8")
    lines = fin.readlines()
    fin.close()
    for line in lines:
      l = line.strip().split("\t")
      if len(l) == 4:
        db[l[0]] = [l[1], l[2], l[3]]
  except IOError:
    print "no location database available"
  return db

def setLocDB(db):
  """ store the db with normalizations of reported locations """
  lines = []
  for l in db.keys():
    lst = [l, db[l][0], unicode(db[l][1]), unicode(db[l][2])]
    line = u"\t".join(lst)
    lines.append(line)
  fout = codecs.open("locdb.txt", "w", "utf-8")
  fout.write( u"\n".join(lines))
  fout.close()

def usersByLoc(seeds):
  """ turn the unsorted seedlist into a dictionary per location """
  out = {}
  for seed in seeds:
    uname = seed[0]
    loc = seed[1]
    try:
      out[loc].append(uname)
    except KeyError:
      out[loc] = [uname]
  return out

def acceptableLocation(l, seeds, haveLocs):
  """ check if the reported location is an acceptable location via normalization
      with the google geocoder """
  stts = getSettings()
  locmin = stts["locmin"]
  out = False
  if len(l) > 0:
    locdb = getLocDB()
    try:
      [place, lat, lng] = locdb[l]
      try:
        if len(haveLocs[place]) < locmin:
          out = [place, lat, lng]
      except:
        out = [place, lat, lng]
    except:
      fin = codecs.open("cities.txt", "r", "utf-8")
      locations = fin.readlines()
      fin.close()
      g = geocoders.GoogleV3()
      try:
        time.sleep(35.0) # sleep a bit so that we do not overdo the geocoder, 
                         #with 35 seconds, you can do 2500 requests a day
        place, (lat, lng) = list(g.geocode(l.encode("utf-8"), 
                                           exactly_one=False))[0]
        for location in locations:
          location = location.strip()
          regex = re.compile(r"\b" + location + r"\b", re.IGNORECASE)
          if len(regex.findall(place)) > 0:
            # check if the amount of locations is not too big
            try:
              if len(haveLocs[place]) < locmin:
                out = [place, lat, lng]
            # if the location is not in haveLocs yet, it's ok
            except KeyError:
              out = [place, lat, lng]
              locdb[l] = [place, lat, lng]
              setLocDB(locdb)
      except Exception, e:
        print "\t", e
  return out

def saveSeeds(seeds):
  """ write out the seedlist """
  out = []
  for seed in seeds:
    out.append( seed[0].strip() + "," + seed[1].strip() )
  fout = codecs.open("seedlist.txt", "w", "utf-8")
  fout.write( u"\n".join(out) )
  fout.close()

def getSeeds(api):
  """ get the seedlist """
  seeds = getPriorSeeds("seedlist.txt")
  milked = []
  stts = getSettings()
  convergence = stts["convergence"]
  while (len(seeds) < convergence):
    seedsample = []
    try:
      seedsample = random.sample(set(seeds), 1)
    except ValueError:
      seedsample = seeds
    milked.extend(seedsample)
    newseeds = getNewSeeds(seedsample, seeds, api)
    seeds.extend(newseeds)
    saveSeeds(seeds)
    print "there are now", len(seeds), "available"
  return seeds

def getTweets(uname, loc):
  """ fetch the tweets of a given user, parameter loc is the standardized
      location for this user """
  out = []

  # call to api
  rls = api.GetRateLimitStatus()
  if rls["resources"]["statuses"]["/statuses/user_timeline"]["remaining"] > 1:
    tl = api.GetUserTimeline(uname, include_entities=False, count=2000)
  else:
    sleeptime = rls["resources"]["statuses"]["/statuses/user_timeline"]["reset"] - time.time()
    print "sleeping for", sleeptime + 5, "seconds"
    time.sleep(sleeptime + 5)
    tl = api.GetUserTimeline(uname, include_entities=False, count=2000)

  print "\tfound", len(tl), "statuses"
  # go through the data that was retrieved from twitter
  for s in tl:
    date = s.created_at # data
    identifier = unicode(s.id) # tweet id
    text = s.text # tweet itself
    reploc = s.GetUser().location # reported location
    if reploc == None:
      reploc = "NA"
    out.append( unicode("<tweet user=\"" + uname + "\" norm_loc=\"" + loc + 
                        "\" rep_loc=\"" + reploc + "\" date=\"" + date + 
                        "\" id=\"" +   identifier + "\">" + text + 
                        "</tweet>") )
  return out

def xmlstore(l):
  """ store a list of tweets from getTweets as xml """
  print "writing out to file"
  out = "<tweets>\n" + "\n".join(l) + "\n</tweets"
  fname = "./tweets/" + hashlib.sha224(out.encode("utf-8")).hexdigest() + ".xml"
  fout = codecs.open(fname, "w", "utf-8")
  fout.write(out)
  fout.close()

def sortSeeds(seeds, sorter):
  """ sort the seeds, currently only biglocationfirst available """
  out = []
  if sorter == "bigLocationsFirst":
    locs = []
    db = {}
    for (uname, loc) in seeds:
      locs.append(loc)
      try:
         db[loc].append(uname)
      except KeyError:
        db[loc] = [uname]
    freqs = Counter(locs)
    while freqs:
      curloc = freqs.most_common(1)[0]
      del freqs[curloc[0]]
      for seed in db[curloc[0]]:
        out.append( (seed, curloc[0]) )
  return out

def getUserNames():
  """ extract from downloaded tweets all the downloaded usernames """
  out = []
  fl = glob.glob("./tweets/*")
  regex = re.compile("user=\"(.+?)\"")
  for f in fl:
    fin = codecs.open(f, "r", "utf-8")
    xml = fin.read()
    fin.close()
    out.extend( regex.findall(xml) )
  return set(out)

def main():
  """ this is where it all starts """
  # get user input from file
  print "reading in settings..."
  stts = getSettings()
  (consumerkey, consumersecret, accesstokenkey, accesstokensecret) = stts["api"]
  
  # initialize the api
  print "initializing Twitter api..."
  api = twitter.Api(consumer_key=consumerkey,
  consumer_secret=consumersecret, 
  access_token_key=accesstokenkey, 
  access_token_secret=accesstokensecret)
  
  # add to the seedlist
  seeds = getSeeds(api)
  print "got all the seeds we need..."
  users_have = getUserNames()
  sortedSeeds = sortSeeds(seeds, "bigLocationsFirst")
  tweetnum = 0
  tweets = []
  for (seed, loc) in sortedSeeds:
    if seed not in users_have:
      print "grabbing tweets for", seed, loc
      tweets.extend( getTweets(seed, loc) )
      if len(tweets) > 10000:
        xmlstore(tweets)
        tweets = []
  xmlstore(tweets)

if __name__ == "__main__":
    main()
