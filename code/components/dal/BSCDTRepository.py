#!/usr/bin/env python3
#
# Abstract factory for accessing storage repositories
# This module is part of the Smart Center Control (SSC) solution
#
# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module imports
import subprocess
import os

from ucis4eq.dal.staticDataAccess import RepositoryABC

################################################################################
# Methods and classes

class BSCDTRepository(RepositoryABC):
    def __init__(self, user, url, path):
        
        # Base command 
        self.baseCmd = "scp" 
        
        # Store the username, url and base path
        self.user = user
        self.url = url
        self.path = path
            
    def authenticate(self):
        pass
    
    def mkdir(self, rpath):
        # Create remote folder
        print("mkdir " + rpath, flush=True)
        remote = self.user + "@" + self.url    

        # Perform the operation
        subprocess.run(["ssh", remote, "mkdir -p", 
                       os.path.join(self.path, rpath)])
                       
    def mkdir(self, rpath):
        # Create remote folder
        print("mkdir " + rpath, flush=True)
        remote = self.user + "@" + self.url    

        # Perform the operation
        subprocess.run(["ssh", remote, "mkdir -p", 
                       os.path.join(self.path, rpath)])                       
                               
    def downloadFile(self, remote, local):
        
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
        
        print("Download: " + remote, flush=True)        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        subprocess.run([self.baseCmd, remote, local])
        
    def uploadFile(self, remote, local):
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
            
        print("Up: " + local, flush=True)
        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        subprocess.run([self.baseCmd, local, remote])
              
    def __del__(self):
        pass
        # TODO: Figure out why the following line is failing
        #free_size = self._client.free()
    
class BSCDTRepositoryBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, BSCDT, **_ignored):
        user = BSCDT["user"]
        url = BSCDT["url"]
        path = BSCDT["path"]
        if not self._instance:
            self._instance = BSCDTRepository(user, url, path)
            
        return self._instance
