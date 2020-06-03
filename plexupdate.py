#!/usr/bin/env python

import urllib
import json
import re
import os
import subprocess
import sys 
import logging

logging.basicConfig(
    filename='/var/log/plexupdate.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


username = str(subprocess.check_output("whoami").strip())
if username != "root":
    logging.critical("You have to be root to run this app, current user is: %s" % (username))
    sys.exit()

url = "https://plex.tv/api/downloads/1.json"
response = urllib.urlopen(url)

currentVersion = '0' 
try:
    currentVersion = subprocess.check_output("dpkg -l | grep -i plexmediaserver", shell=True)
    currentVersion = re.search(r'(\d+\.)+\d+', str(currentVersion)).group()
    logging.info("Installed version is: %s" % (currentVersion))
    #print("Current version is: %s" % (currentVersion))
except Exception as e:
    logging.critical("Plex is not Installed")

try:
    releases = json.loads(response.read())['computer']['Linux']['releases']
    for release in releases:
        if release['distro'] == 'ubuntu' and release['build'] == 'linux-ubuntu-x86_64':
            #print(release['label'])
            #print(release['url'])
            version = re.search(r'(\d+\.)+\d+', release['url']).group()
            fileVersionName = "/var/tmp/plex_" + version + ".deb"
            if currentVersion != version:
                logging.info("Updating to version: %s" % (version))
                debfile = urllib.URLopener()
                debfile.retrieve(release['url'], fileVersionName)
                logging.info("Downloaded file to: %s" % (fileVersionName))
                subprocess.check_output("/usr/sbin/service plexmediaserver stop", shell=True)
                subprocess.check_output("sudo dpkg -i %s" % (fileVersionName), shell=True)
                subprocess.check_output("rm %s" % (fileVersionName), shell=True)
                subprocess.check_output("/usr/sbin/service plexmediaserver start", shell=True)
                logging.info("Done with the Update")
            else:
                logging.info("No update is needed")
            break
except Exception as e:
    logging.critical(e)
