
#!/usr/bin/python3
import pprint
import http.cookiejar, urllib.request
import urllib
import os

def get_cookie(jar, name):
	return [cookie for cookie in jar if cookie.name == name][0]

# Settings
funky_user = ""
if os.environ.get('FUNKY_USER'):
	print("Setting username from FUNKY_USER")
	funky_user = os.environ.get('FUNKY_USER')
funky_pass = ""
if os.environ.get('FUNKY_PASS'):
	print("Setting password from FUNKY_PASS")
	funky_pass = os.environ.get('FUNKY_PASS')

# Cookies
cookies = http.cookiejar.LWPCookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
urllib.request.install_opener(opener)

# Authenticate user
print("logging in")
login_url = "http://forum.funkysouls.com/index.php?s=&act=Login&CODE=01"
login_values = {"UserName" : funky_user, 
          "PassWord" : funky_pass}
login_data = urllib.parse.urlencode(login_values)
binary_login = login_data.encode('ascii')
login_req = urllib.request.Request(login_url, binary_login)
urllib.request.urlopen(login_req)

# Check user is logged in
if not get_cookie(cookies, 'pass_hash') and not get_cookie(cookies, 'member_id'):
	print("Couldn't login, wrong credentials?")
	exit(1)
print("\tlogged in")

# Destroy our cookie jar
cookies.clear()
