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
    def __init__(self, user, url, path, resources, setup=None, proxy=None):
        
        # Base command 
        self.baseCmd = "ssh" 

        if proxy:
            self.proxyFlag = "-o"
            self.proxyCmd = "ProxyCommand=ssh -W %h:%p " + proxy
        else:
            self.proxyFlag = ""
            self.proxyCmd = ""
        
        # Store the username, url, base path and resources
        self.user = user
        self.url = url
        self.path = path
        self.resources = resources
        self.setup = setup
        
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

        # Check for and error
        command_trials = 0
        while True:
            process = subprocess.run(list(filter(None, command)),
                                     stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     encoding='utf8')

            if process.returncode != 0:
                if command_trials < 3:
                    print("\nWARNING: Command '" + self.baseCmd + " " + remote + " " + tcmd
                          + "' failed. Error: " + process.stderr + "Retrying in 15 seconds.", flush=True)
                    time.sleep(15)
                    command_trials += 1
                    continue
                else:
                    raise Exception("Command '" + self.baseCmd + " " + remote + " "
                                   + tcmd + "' failed three times in a row. Error: " + process.stderr)
            else:
                break


        # Obtain the job ID
        jobId = [x.strip() for x in process.stdout.split(' ')][3]
        
        thread = threading.Thread(target=self._waitForSlurmJob, args=(jobId,path))
        thread.start()

        # Wait for the process to finish
        timeout = 5
        while not self.resultAvailable.wait(timeout=timeout):
            #print('\r{}'.format(self.message), end='', flush=True)
            pass
            
    # Wait for a Slurm job to finish
    def _waitForSlurmJob(self, jobId, rundir):

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
                                      
            # Check for a connection error:
            # if the connection fails, wait for 15 s and try to reconnect
            if process.returncode != 0:
                time.sleep(60)
                print("\nWARNING: Command that checks the job status '" + self.baseCmd + " " + remote + " " + cmd
                      + "' failed. Error: " + process.stderr + "Retrying in 60 seconds.", flush=True)
                continue
                # raise Exception("Command '" + self.baseCmd + " " + remote + " "
                #                 + cmd + "' failed. Error: " + process.stderr)
            
            # Set a message
            self.message = process.stdout.rstrip()

            # Stop condition:
            # if the job is not in the queue, stop checking and assume that the job is finished
            # MPC ToDo here if the job is not in the queue it is assumed to be finished successfully,
            # but it is not actually always true. Need a different mechanism of checking and/or retrying.
            if process.stdout == "":
                command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, "find", rundir + "/SUCCESS"]

                process = subprocess.run(list(filter(None, command)),
                                         stdout=subprocess.PIPE,
                                         stdin=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
                if "SUCCESS" in process.stdout:
                    # Results are available
                    print("INFO: the job submitted in %s completed successfully." %rundir)
                    self.resultAvailable.set()
                    break
                else:
                    # Results are not available, the job is not in the queue but seems like it did not complete
                    # successfully either.

                    # MPC Dump info from .e and .o to the log?
                    command_e = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, "cat", rundir + "/*.e"]
                    command_o = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, "cat", rundir + "/*.o"]
                    process_e = subprocess.run(list(filter(None, command_e)),
                                             stdout=subprocess.PIPE,
                                             stdin=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             encoding='utf8')
                    process_o = subprocess.run(list(filter(None, command_o)),
                                             stdout=subprocess.PIPE,
                                             stdin=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             encoding='utf8')

                    print("\nWARNING: something went wrong in %s." %rundir)
                    print("\nWARNING: stderr: \n" + process_e.stdout)
                    print("\nWARNING: stdout: \n" + process_o.stdout)

                    self.resultAvailable.clear()
                    raise Exception(
                        "The job submitted in %s seems to not have completed successfully. Automatic "
                        "resubmission is not implemented yet, please check the error manually." %rundir)

            else:
                time.sleep(60)

