#!/usr/bin/env python3

from bs4 import BeautifulSoup
from urllib import request
import re
import subprocess
import zipfile
import os
import logging
import sys




class UpdateAgentDVR():
    def __init__(self):
        self.install_dir = "/opt/agentdvr/"
        self.install_fileversion = self.install_dir + "/version.txt"
        self.url = "https://www.ispyconnect.com/download.aspx"
        self.download_dir = "/var/tmp/agentdvr_{}.zip"
        self.download_url = ""
        self.latest_version = None
        self.current_version = None

    def get_latest_version(self):
        # Download land page for web scraping
        response = request.urlopen(self.url)
        soup = BeautifulSoup(response.read(), 'html.parser')

        for link in soup.find_all('a'):
            zip_href = link.get('href')
            if 'zip' in zip_href and 'Linux' in zip_href:
                # The correct zip file has been found
                self.download_url = zip_href
                m = re.search(r'(\d+_?)+', zip_href)
                if m:
                    self.latest_version = m.group(0)[3:].replace("_", ".")
        self.download_dir = self.download_dir.format(self.latest_version)
        logging.info("Latest version is: {}".format(self.latest_version))
        return self.latest_version

    def get_current_version(self):
        if os.path.exists(self.install_fileversion):
            with open(self.install_fileversion, 'r') as version_file:
                self.current_version = version_file.read()
        logging.info("Current version is: {}".format(self.current_version))
        return self.current_version

    def download(self):
        logging.info("Downloading file {} to dir {}".format(
            self.download_url,
            self.download_dir))
        request.urlretrieve(self.download_url, self.download_dir)

    def install(self):
        logging.info("Extracting file to the installation directory {}".format(
            self.install_dir))
        # Download file
        with zipfile.ZipFile(self.download_dir, 'r') as zip_ref:
            zip_ref.extractall(self.install_dir)

        # Save installed version
        with open(self.install_fileversion, 'w') as version_file:
            version_file.write(self.latest_version)

        self.restart_service()

    def restart_service(self):
        service_file = "/etc/systemd/system/agentdvr.service"
        if not os.path.exists(service_file):
            logging.info("Service not found, creating new to: {}".format(service_file))
            with open(service_file, 'w') as serv:
                serv.write("[Unit]\n")
                serv.write("Description=Agent DVR Server\n\n")
                serv.write("[Service]\n")
                serv.write("ExecStart=/usr/bin/dotnet {}/Agent.dll\n".format(self.install_dir))
                serv.write("Restart=on-abort\n\n")
                serv.write("[Install]\n")
                serv.write("WantedBy=multi-user.target\n")
        subprocess.check_output("/usr/sbin/service agentdvr restart", shell=True)


username = str(subprocess.check_output("whoami").decode('utf-8').strip())
if username != "root":
    logging.critical("You have to be root to run this app, current user is: {}".format(username))
    sys.exit()


logging.basicConfig(
    filename='/var/log/updater.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

agentdvr = UpdateAgentDVR()
latest_version = agentdvr.get_latest_version()
current_version = agentdvr.get_current_version()
if current_version != latest_version and latest_version is not None:
    agentdvr.download()
    agentdvr.install()
