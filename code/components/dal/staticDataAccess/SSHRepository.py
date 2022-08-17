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

from ucis4eq.dal.staticDataAccess.staticDataAccess import RepositoryABC

################################################################################
# Methods and classes

class SSHRepository(RepositoryABC):
    def __init__(self, user, url, path, proxy=None):
        
        # Base command 
        self.baseCmd = "scp" 
            
        if proxy:
            self.proxyFlag = "-o"
            self.proxyCmd = "ProxyCommand=ssh -W %h:%p " + proxy
        else:
            self.proxyFlag = ""
            self.proxyCmd = ""
            
        # Store the username, url and base path
        self.user = user
        self.url = url
        self.path = path
            
    def authenticate(self):
        pass
    
    def mkdir(self, rpath):    
        
        # Create remote folder
        #print("mkdir " + rpath, flush=True)
        remote = self.user + "@" + self.url    

        # Perform the operation
        command = ["ssh", self.proxyFlag, self.proxyCmd, remote, "mkdir -p", 
                       os.path.join(self.path, rpath)]
        subprocess.run(list(filter(None, command)))
        
    def tree(self, rpath):    
        
        # Create remote folder
        #print("mkdir " + rpath, flush=True)
        remote = self.user + "@" + self.url    

        # Perform the operation
        command = ["ssh", self.proxyFlag, self.proxyCmd, remote, "find", 
                       os.path.join(self.path, rpath)]
        output=subprocess.run(list(filter(None, command)), capture_output=True)        

        # Parse output and return
        return output.stdout.decode("utf-8").split("\n")[:-1]
                 
    def downloadFile(self, remote, local):
        
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
        
        #print("Download: " + remote, flush=True)        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, local]
        subprocess.run(list(filter(None, command)))
        
    def uploadFile(self, remote, local):
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
            
        #print("Upload: " + local, flush=True)
        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, local, remote]
        subprocess.run(list(filter(None, command)))
              
    def __del__(self):
        pass
        # TODO: Figure out why the following line is failing
        #free_size = self._client.free()
    
class BSCDTRepositoryBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, BSC_DT, **_ignored):
        
        user = BSC_DT["user"]
        url = BSC_DT["url"]
        path = BSC_DT["path"]
        if not self._instance:
            self._instance = SSHRepository(user, url, path)
            
        return self._instance
        
class ETHDAINTRepositoryBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, ETH_DAINT, **_ignored):
        
        user = ETH_DAINT["user"]
        url = ETH_DAINT["url"]
        path = ETH_DAINT["path"]
        proxy = ETH_DAINT["proxy"]
        
        if not self._instance:
            self._instance = SSHRepository(user, url, path, proxy)
            
        return self._instance        
