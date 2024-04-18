#!/usr/bin/env python3

# Abstract factory for accessing storage repositories
# This module is part of the Smart Center Control (SSC) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Josep de la Puente, Juan Esteban Rodriguez, Marisol
# Monterrubio, Marta Pienkowska.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 3. Neither the name(s) of the copyright holder(s) nor the name(s) of its
# contributor(s) may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND CONTRIBUTOR(S) “AS
# IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S) OR CONTRIBUTOR(S) BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ###############################################################################
# Module imports
from ucis4eq.dal.staticDataAccess.staticDataAccess import RepositoryABC

# Load NextCloud API
from webdav3.client import Client

# ###############################################################################
# Methods and classes

class WebDavRepository(RepositoryABC):
    def __init__(self, user, passwd, url):
        
        # Store the username
        self.user = user
            
        # Create a client
        options = {
         'webdav_hostname': url,
         'webdav_login':    user,
         'webdav_password': passwd,
         'verbose': True
        }
        self._client = Client(options)
            
    def authenticate(self):
        pass
    
    def mkdir(self, rpath):
        # Create remote folder
        self._client.mkdir(rpath)
        
    def tree(self, rpath):
        # List files from a remote path
        print("WARNING: Obtaining list of files from WebDavRepository is unsuported yet")
        return None

    def downloadFile(self, remote, local):
        # Download file
        print("Downloading webdav " + str(remote) + " to " + str(local) )
        self._client.download_sync(remote_path=remote, local_path=local)
        
    def uploadFile(self, remote, local):
        # Upload file
        print(f"Uploading '{local}' to '{remote}'")
        self._client.upload_sync(remote_path=remote, local_path=local)
        
    def __del__(self):
        pass
        # TODO: Figure out why the following line is failing
        #free_size = self._client.free()
    
class BSCB2DROPRepositoryBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, BSC_B2DROP, **_ignored):
        user = BSC_B2DROP["user"]
        passw = BSC_B2DROP["pass"]
        url = BSC_B2DROP["url"]
        
        if not self._instance:
            accessCode = self.authorize(
                user, passw)
            self._instance = WebDavRepository(user, passw, url)
        return self._instance

    def authorize(self, key, secret):
        return 'B2DROP_ACCESS_CODE'
