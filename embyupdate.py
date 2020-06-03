#!/usr/bin/env python3

from urllib import request
import json
import re
import subprocess
import sys 
import logging

logging.basicConfig(
    filename='/var/log/embyupdate.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

username = str(subprocess.check_output("whoami").strip().decode('ascii'))
if username != "root":
    logging.critical("You have to be root to run this app, current user is: %s" % (username))
    sys.exit()

url = "https://api.github.com/repos/MediaBrowser/Emby.Releases/releases/latest"
response = request.urlopen(url).read()
newVersion = json.loads(response)['tag_name']
fileNewVersion = '/var/tmp/emby_{0}.deb'.format(newVersion)
urlNewVersion = 'https://github.com/MediaBrowser/Emby.Releases/releases/download/{0}/emby-server-deb_{0}_amd64.deb'.format(newVersion)
#print newVersion
#print fileNewVersion
#print urlNewVersion


installedVersion = '0' 
try:
    installedVersion = subprocess.check_output("/usr/bin/dpkg -l | grep -i emby-server", shell=True)
    installedVersion = re.search(r'(\d+\.)+\d+', str(installedVersion)).group()
    logging.info("Installed version is: %s" % (installedVersion))
except Exception as e:
    logging.critical("Emby is not Installed")

if installedVersion != newVersion:
    try:
        logging.info("Updating to version: %s" % (newVersion))
        request.urlretrieve(urlNewVersion, fileNewVersion)
        logging.info("Downloaded file to: %s" % (fileNewVersion))
        logging.debug(subprocess.check_output("/usr/sbin/service emby-server stop", shell=True))
        logging.debug(subprocess.check_output("sudo /usr/bin/dpkg -i %s" % (fileNewVersion), shell=True))
        logging.debug(subprocess.check_output("rm %s" % (fileNewVersion), shell=True))
        logging.debug(subprocess.check_output("/usr/sbin/service emby-server start", shell=True))
        logging.info("Done with the Update")
    except Exception as e:
        logging.critical(e)
else:
    logging.info("No update is needed")
