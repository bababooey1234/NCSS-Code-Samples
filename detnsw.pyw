# run by task scheduler, this automatically logs into the portal for the
# "Secured Internet at Edge" whenever I connect to school wifi.

# not my details, an account with elevated permissions.
user = "srv7416circulation"
pswd = "FawnHippo4"

import requests
sesh = requests.Session()
url = "https://edgeportal.det.nsw.edu.au:6082/php/uid.php?vsys=1&rule=0"

# get preauthid
response = sesh.get(url)
preauthid = response.text.split('\n')[127][30:46]

# send details
response = sesh.post(
  url,
  data=f"inputStr=&escapeUser={user}&preauthid={preauthid}&user={user}&passwd={pswd}&ok=Login"
)
