#!/usr/bin/env python3
#
# Slurm specialization launcher
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
import os
import time
import uuid
import subprocess
import threading

from abc import ABC, abstractmethod
from ucis4eq.launchers.runnerABC import RunnerABC

################################################################################
# Methods and classes

class SlurmRunnerABC(RunnerABC, ABC):

    # Some attributes
    message = ""
    time = 0
    resultAvailable = None
    type = "slurm"
    uuid = uuid.uuid1()
    
    # Initialization method    
    def __init__(self, user, url, path, proxy=None):
        
        # Base command 
        self.baseCmd = "ssh" 

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
        
        # Initialize the synchronizerpos
        self.resultAvailable = threading.Event()

    # Method for obtaining the spefific MPI command (srun, mpirun, etc...)           
    def getMPICommand(self):
        return "/usr/bin/srun --ntasks=$SLURM_NTASKS --ntasks-per-node=$SLURM_NTASKS_PER_NODE "        
            
    # Enqueue a process and wait
    def run(self, path, cmd):

        # Remote connection
        remote = self.user + "@" + self.url  
        
        tcmd = "cd " + path + "; sbatch " + cmd

        # Run the command and wait
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, tcmd]
        process = subprocess.run(list(filter(None, command)),
                                  stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  encoding='utf8')

        # Check for and error
        if process.returncode != 0:
            raise Exception("Command '" + self.baseCmd + " " + remote + " " 
                            + tcmd + "' failed. Error: " + process.stderr)

        # Obtain the job ID
        jobId = [x.strip() for x in process.stdout.split(' ')][3]
        
        thread = threading.Thread(target=self._waitForSlurmJob, args=(jobId,))
        thread.start()

        # Wait for the process to finish
        timeout = 5
        while not self.resultAvailable.wait(timeout=timeout):
            #print('\r{}'.format(self.message), end='', flush=True)
            pass
            
    # Wait for a Slurm job to finish
    def _waitForSlurmJob(self, jobId):

        # Remote connection    
        remote = self.user + "@" + self.url    

        cmd = 'squeue -h -o "Slurm job %T (%M of %l)" --job ' + jobId + ''
        
        # Delay for avoiding check the job before this is registered 
        time.sleep(5)
        
        # Wait for the job to finish
        while True:
            # Query for the job state
            command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, cmd]
            process = subprocess.run(list(filter(None, command)),
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      encoding='utf8')
                                      
            # Check for and error
            if process.returncode != 0:
                raise Exception("Command '" + self.baseCmd + " " + remote + " " 
                                + cmd + "' failed. Error: " + process.stderr)
            
            # Set a message
            self.message = process.stdout.rstrip()

            # Stop condition
            if process.stdout == "":
                break
            else:
                time.sleep(5)

        # Results are available
        self.resultAvailable.set()                         
