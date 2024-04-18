#!/usr/bin/env python3

# Abstract factory for accessing storage repositories
# This module is part of the Smart Center Control (SSC) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Josep de la Puente, Juan Esteban Rodriguez

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
import subprocess
import os
import time

from ucis4eq.dal.staticDataAccess.staticDataAccess import RepositoryABC

# ###############################################################################
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
        command_trials = 0
        while True:
            process = subprocess.run(list(filter(None, command)),
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      encoding='utf8')

            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + "ssh " + self.proxyFlag + " " + self.proxyCmd + " " + remote
                          + " mkdir -p " + os.path.join(self.path, rpath)
                          + "' failed. Error: " + process.stderr
                          + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    raise Exception("Command '" + "ssh " + self.proxyFlag + " " + self.proxyCmd + " " + remote
                                    + " mkdir -p " + os.path.join(self.path, rpath)
                                    + "' failed three times in a row. Error: "
                                    + process.stderr)
            else:
                break

    def tree(self, rpath):    
        
        # Create remote folder
        #print("mkdir " + rpath, flush=True)
        remote = self.user + "@" + self.url    

        # Perform the operation
        command = ["ssh", self.proxyFlag, self.proxyCmd, remote, "find", 
                       os.path.join(self.path, rpath)]

        command_trials = 0
        while True:
            process = subprocess.run(list(filter(None, command)), capture_output=True)

            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + "ssh " + self.proxyFlag + " " + self.proxyCmd
                          + " " + remote + " find " + os.path.join(self.path, rpath)
                          + "' failed. Error: " + process.stderr.decode("utf-8")#.split("\n")[:-1]
                          + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    raise Exception("Command '" + "ssh " + self.proxyFlag + " " + self.proxyCmd
                                    + " " + remote + " find " + os.path.join(self.path, rpath)
                                    + "' failed three times in a row. Error: "
                                    + process.stderr.decode("utf-8"))#.split("\n")[:-1])
            else:
                break

        # Parse output and return
        return process.stdout.decode("utf-8").split("\n")[:-1]
                 
    def downloadFile(self, remote, local):
        
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
        
        #print("Download: " + remote, flush=True)        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, local]

        command_trials = 0
        while True:
            process = subprocess.run(list(filter(None, command)),
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      encoding='utf8')

            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + self.baseCmd + " " + self.proxyFlag + " "
                          + self.proxyCmd + " " + remote + " " + local
                          + "' failed. Error: " + process.stderr
                          + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    raise Exception("Command '" + self.baseCmd + " " + self.proxyFlag + " "
                                    + self.proxyCmd + " " + remote + " " + local
                                    + "' failed three times in a row. Error: "
                                    + process.stderr)
            else:
                break
        
    def uploadFile(self, remote, local):
        # Build the remote filename
        if not os.path.isabs(remote):
            remote = os.path.join(self.path, remote)
            
        #print("Upload: " + local, flush=True)
        
        remote = self.user + "@" + self.url + ":" + remote
    
        # Perform the operation
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, local, remote]

        command_trials = 0
        while True:
            process = subprocess.run(list(filter(None, command)),
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      encoding='utf8')

            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + self.baseCmd + " " + self.proxyFlag + " "
                          + self.proxyCmd + " " + local + " " + remote
                          + "' failed. Error: " + process.stderr
                          + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    print(process.stderr)
                    raise Exception("Command '" + self.baseCmd + " " + self.proxyFlag + " "
                                    + self.proxyCmd + " " + local + " " + remote
                                    + "' failed three times in a row. Error: "
                                    + process.stderr)
            else:
                break
              
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
