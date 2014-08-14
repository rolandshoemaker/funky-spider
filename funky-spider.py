#!/usr/bin/python3
import pprint
import http.cookiejar, urllib.request
import urllib
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def get_cookie(jar, name):
	return [cookie for cookie in jar if cookie.name == name][0]

VERSION = '0.01'
print(colors.HEADER+"funky spider v"+VERSION+colors.ENDC)

# Settings
print(colors.OKBLUE+"Setting settings..."+colors.ENDC)
allowed_hosts = ["zippyshare", "mediafire"]
funky_user = ""
if os.environ.get('FUNKY_USER'):
	print(colors.OKGREEN+"\tSetting username from FUNKY_USER"+colors.ENDC)
	funky_user = os.environ.get('FUNKY_USER')
funky_pass = ""
if os.environ.get('FUNKY_PASS'):
	print(colors.OKGREEN+"\tSetting password from FUNKY_PASS"+colors.ENDC)
	funky_pass = os.environ.get('FUNKY_PASS')
funky_threads = ["http://forum.funkysouls.com/index.php?act=ST&f=71&t=355890&s="]

# Cookies
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

# Checking threads
print(colors.OKBLUE+"Checking threads"+colors.ENDC)
for thread in funky_threads:
	thread_req = urllib.request.Request(thread)
	data = urllib.request.urlopen(thread_req)
	if data.status == 200:
		print(colors.OKGREEN+"\tparsing html for links"+colors.ENDC)
		html = str(data.read())
		trans = str.maketrans('[]\\', '   ')
		html = html.translate(trans)
		#soup = BeautifulSoup(str(data.read()))
		link_list = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)
		for link in link_list:
			if re.match('https?:\/\/forum\.funkysouls\.com\/go\.php\?(.+)', link):
				full = re.search('https?:\/\/forum\.funkysouls\.com\/go\.php\?(.+)', link)
				m = re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', full.group(1))
				domain = urlparse(m.group(0)).hostname.split('.')
				if len(domain) is 3 and domain[1] in allowed_hosts:
					print("\t\t"+m.group(0))
				elif len(domain) is 2 and domain[0] in allowed_hosts:
					print("\t\t"+m.group(0))

# Destroy our cookie jar
cookies.clear()
