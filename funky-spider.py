#!/usr/bin/python3
import pprint
import http.cookiejar, urllib.request
import urllib
import os
import re
import time
import math
#from sqlalchemy import *
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from urllib.error import URLError, HTTPError

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class AppURLopener(urllib.request.FancyURLopener):
	version = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"

urllib._urlopener = AppURLopener()

def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
	def dec(func):
		def f2(*args, **kwargs):
			mydelay = delay
			tries = range(max_tries)
			#tries.reverse()
			for tries_remaining in tries:
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					if tries_remaining > 0:
						if hook is not None:
							hook(tries_remaining, e, mydelay)
							sleep(mydelay)
							mydelay = mydelay * backoff
						else:
							raise
				else:
					break
		return f2
	return dec
@retries(max_tries=15, delay=3, backoff=2, exceptions=(URLError, HTTPError))
def retry_urlopen(url):
	return urllib.request.urlopen(url)

zippy_dead = 0
zippy_alive = []
def zippy_attack(url):
	global zippy_dead
	global zippy_alive
	zippy_req = urllib.request.Request(url)
	try:
		zippy_data = retry_urlopen(zippy_req)
		if zippy_data.status == 200:
			zippy_html = str(zippy_data.read())
			zippy_soup = BeautifulSoup(zippy_html)
			if not zippy_soup.title.text == "Zippyshare.com - ":
				zippy_dl = zippy_soup.find('a', id="dlbutton")
				if not zippy_dl is None:
					zippy_js = zippy_soup.find_all('script')
					for js in zippy_js:
						if re.match('\\\\n   var somffunction', js.text):
							a = re.search('var a = (\d*)\;', js.text)
							if a.group(1):
								secret = int(a.group(1))
								download_secret = str(int((secret%78956)*(secret%3)+18))
								if not download_secret == '18':
									url_info = url.split('/')
									download_server = str(url_info[2].split('.')[0])
									download_file = str(url_info[4])
									zippy_title = zippy_soup.title.text.split(' - ')
									zippy_title.pop(0)
									download_name = " ".join(zippy_title)
									download_name = urllib.parse.quote(download_name)
									print(colors.OKGREEN+"\tDirect link: "+download_server+".zippyshare.com/d/"+download_file+"/"+download_secret+"/"+download_name+colors.ENDC)
									# either download or add to list to be downloaded... (also do mysql stuff to say we've seen it so we don't look again)
									zippy_alive.append(download_server+".zippyshare.com/d/"+download_file+"/"+download_secret+"/"+download_name)
								else:
									print(colors.WARNING+"\tDownload secret is suspect, let's try again later"+colors.ENDC)
									# add to table to retry
			else:
				print(colors.WARNING+"\tDead link"+colors.ENDC)
				zippy_dead = zippy_dead+1
				# Add to mysql table as dead

	except URLError:
		print(colors.WARNING+"\tConnection refused, let's add this link to a list and try it again later"+colors.ENDC)
		time.sleep(5)
					
def get_cookie(jar, name):
	return [cookie for cookie in jar if cookie.name == name][0]

VERSION = '0.01'
print(colors.HEADER+"funky spider v"+VERSION+colors.ENDC)

# Settings
print(colors.OKBLUE+"Setting settings..."+colors.ENDC)
allowed_hosts = ["zippyshare", "mediafire", "ifolder"]

funky_user = ""
if os.environ.get('FUNKY_USER'):
	print(colors.OKGREEN+"\tSetting username from FUNKY_USER"+colors.ENDC)
	funky_user = os.environ.get('FUNKY_USER')

funky_pass = ""
if os.environ.get('FUNKY_PASS'):
	print(colors.OKGREEN+"\tSetting password from FUNKY_PASS"+colors.ENDC)
	funky_pass = os.environ.get('FUNKY_PASS')

funky_threads = ["http://forum.funkysouls.com/index.php?act=ST&f=71&t=355890"] #, "http://forum.funkysouls.com/index.php?s=&act=ST&f=71&t=11701"]

funky_db = "sqlite:///funky.db"
if os.environ.get('FUNKY_DB'):
	print(colors.OKGREEN+"\tSetting DB URI from FUNKY_DB"+colors.ENDC)
	funky_db = os.environ.get('FUNKY_DB')

# Database
#db = create_engine(funky_db)
#threads = Table()
#links = Table()
#files = Table()

# Cookies & opener
print(colors.OKBLUE+"Making a cookie jar..."+colors.ENDC)
cookies = http.cookiejar.LWPCookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
urllib.request.install_opener(opener)

# Authenticate user
print(colors.OKBLUE+"Attempting to Log in"+colors.ENDC)
login_url = "http://forum.funkysouls.com/index.php?s=&act=Login&CODE=01"
login_values = {"UserName" : funky_user, 
          "PassWord" : funky_pass}
login_data = urllib.parse.urlencode(login_values)
binary_login = login_data.encode('ascii')
login_req = urllib.request.Request(login_url, binary_login)
urllib.request.urlopen(login_req)

# pprint.pprint(cookies)
# Check user is logged in
if not get_cookie(cookies, 'pass_hash') and not get_cookie(cookies, 'member_id'):
	print(colors.WARNING+"Couldn't login, wrong credentials?"+colors.ENDC)
	exit(1)
print(colors.OKGREEN+"\tLogged in"+colors.ENDC)

# Attack lists
zippy_list = []

# Checking threads
print(colors.OKBLUE+"Checking threads"+colors.ENDC)
for thread in funky_threads:
	thread_req = urllib.request.Request(thread)
	data = urllib.request.urlopen(thread_req)
	if data.status == 200:
		html = str(data.read())
		soup = BeautifulSoup(html)
		title = soup.title.text.split(" :: ")
		print(colors.OKGREEN+"\t\tParsing html for thread: "+title[0]+colors.ENDC)

		# Check how many pages
		for nav in soup.find_all('a'):
			if nav.string == "Last »":
				length = parse_qs(urlparse(nav['href']).query)['st'][0]
				length = length.replace('\\', '')
				length = length.replace('\'', '')
				length = int(length)
				print(colors.OKGREEN+"\t\tPages: "+str(int(length/15))+colors.ENDC)
				break

		#for (i = 0;i<=length;i+15):
		for i in range(0, int(length), 15):			
			try:
				pg_num_data = urllib.parse.urlencode({"st": i})
				pg_num = pg_num_data.encode('ascii')
				page_req = urllib.request.Request(thread, pg_num)
				page_data = retry_urlopen(page_req) #urllib.request.urlopen(page_req)
				page_html = str(page_data.read())
				page_soup = BeautifulSoup(page_html)
	
				print(colors.OKGREEN+"\t\t\tPage "+str(int((i/15)+1))+colors.ENDC)

				trans = str.maketrans('[]\\', '   ')
				page_html = page_html.translate(trans)
				link_list = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', page_html)
				for link in link_list:
					if re.match('https?:\/\/forum\.funkysouls\.com\/go\.php\?(.+)', link):
						full = re.search('https?:\/\/forum\.funkysouls\.com\/go\.php\?(.+)', link)
						m = re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', full.group(1))
						if not m is None:
							domain = urlparse(m.group(0)).hostname.split('.')
							# Also check if it's already in mysql table, then push urls into a list 
							if len(domain) is 3 and domain[1] in allowed_hosts:
								print(colors.FAIL+"\t\t\t"+m.group(0)+colors.ENDC)
								if domain[1] == 'zippyshare':
									zippy_list.append(m.group(0))
								
							elif len(domain) is 2 and domain[0] in allowed_hosts:
								print(colors.FAIL+"\t\t\t"+m.group(0)+colors.ENDC)
								if domain[1] == 'zippyshare':
        	                                                        zippy_list.append(m.group(0))
				time.sleep(1) # let's be somewhat courteous
			except URLError:
				print(colors.WARNING+"\tConnection refused, let's add this orphaned thread page to a list and try it again later"+colors.ENDC)
				time.sleep(5)

# (after finished building link list)
# Execute each attack to download all files in link list (if dead link point that out in mysql...)
print(colors.OKBLUE+"Attempting to create direct zippyshare links, list length: "+str(len(zippy_list))+colors.ENDC)
for zippy_download in zippy_list:
	# check if in mysql table first! (could also do in zippy attack function...)
	zippy_attack(zippy_download) 
	time.sleep(3) # let's be somewhat courteous
print("Alive: "+str(len(zippy_alive))+", Dead: "+str(zippy_dead)+", Health: "+str(len(zippy_alive)/(len(zippy_alive)+zippy_dead))*100)
# Extract files to temp dir, check if they have ID3 info, if not go to more extreme measures, store info in mysql database, if we get duplicate just delete it

# Move remaining good files to final resting place, could do basic tagging/organization

# Destroy our cookie jar
cookies.clear()
