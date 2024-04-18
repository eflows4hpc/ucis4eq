#!/usr/bin/env python3

# Slurm specialization launcher
# This module is part of the Smart Center Control (SSC) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

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

################################################################################
# Module imports
import os
import time
import subprocess

from ucis4eq.launchers.runnerABC import RunnerABC

################################################################################
# Methods and classes

class LocalRunner(RunnerABC):

    # Some attributes
    time = 0
    
    # Initialization method    
    def __init__(self, user, url, path):
        
        # Base command 
        self.baseCmd = "ssh" 
        
        # Store the username, url and base path
        self.user = user
        self.url = url
        self.path = path     
            
    # Obtain the spefific rules for a local script    
    def getRules(self, stage):
        
        # Return the set of instructions
        return []

    # Obtain the spefific MPI command (srun, mpirun, etc...)           
    def getMPICommand(self):
        pass
        
    # Obtain environment setup (module loads, PATH, conda environmnet, etc ...)
    def getEnvironmentSetup(self, stage):
        pass
        
    # Run locally and wait
    def run(self, cmd):

        command_trials = 0
        while True:
            # Run the command and wait
            process = subprocess.run(cmd, stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     encoding='utf8')
            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + cmd
                          + "' failed. Error: " + process.stderr + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    raise Exception("Command '" + cmd
                                   + "' failed three times in a row. Error: " + process.stderr)
            else:
                break
        
class LocalRunnerBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, LOCAL, **_ignored):
        user = LOCAL["user"]
        url = LOCAL["url"]
        path = LOCAL["path"]
        if not self._instance:
            self._instance = LocalRunner(user, url, path)
            
        return self._instance
