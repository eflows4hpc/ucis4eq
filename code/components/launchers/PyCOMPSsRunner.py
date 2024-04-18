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

# ###############################################################################
# Module imports
import os
import time
import uuid
import subprocess
import threading

from abc import ABC, abstractmethod
from ucis4eq.launchers.runnerABC import RunnerABC

# ###############################################################################
# Methods and classes

class PyCOMPSsRunner(RunnerABC, ABC):

    # Some attributes
    message = ""
    time = 0
    resultAvailable = None
    type = "ssh"
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
    
    # Obtain the spefific rules for a slurm Script    
    def getRules(self, stage):
        
        # Initialize list of instructions
        cmd = []
        
        # Select the resources for the given stage
        # TODO: Control that provided stage exist
        args = self.resources[stage]
        
        # Check if a job name was provided
        if "name" in args.keys():
            name = args['name']
        else:
            name = stage

        # Build command
        cmd = []
        cmd.append("enqueue_compss")
        cmd.append("-d")
        cmd.append("--num_nodes=" + str(args['nodes']))
        cmd.append("--job_name=" + name)
        cmd.append("--exec_time="+ str(args['wtime']))
        cmd.append("--cpus_per_node=" + str(args['tasks-per-node']))
        cmd.append("--worker_in_master_cpus="+ str(args['tasks-per-node']))
        cmd.append("--qos=" + args['qos'])
     
        
        if "constraint" in args.keys():
            cmd.append("--constraint=" + args['constraint'])
            
        #lines.append("#SBATCH --partition=main")
        #lines.append("#SBATCH --reservation=ChEESE21_test")       
        
        # Return the set of arguments
        return cmd

    # Method for obtaining environment setup (module loads, PATH, conda environmnet, etc ...)
    def getEnvironmentSetup(self, stage):
        # Initialize list of instructions
        lines = []
        
        # TODO: Control that provided stage exist
        args = self.resources[stage]
        
        add_lines = args['environment']

        for line in add_lines:
            lines.append(line)
        
        return lines
    
    # Method for obtaining the spefific MPI command (srun, mpirun, etc...)           
    def getMPICommand(self):
        return "mpirun "        
            
    # Enqueue a process and wait
    def run(self, path, cmd):

        # Remote connection
        remote = self.user + "@" + self.url  
        
        tcmd = "cd " + path + "; sh " + cmd

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
        jobId = self._parseJobId(process.stdout)
        
        thread = threading.Thread(target=self._waitForJob, args=(jobId,))
        thread.start()

        # Wait for the process to finish
        timeout = 5
        while not self.resultAvailable.wait(timeout=timeout):
            print('\r{}'.format(self.message), end='', flush=True)
            # pass

        self.check_job_status(jobId)

    #TODO: Parse Job Id from the PyCOMPSs output         
    def _parseJobId(self,out):
        print("Returned:")
        # print(str(out))
        print(type(out))
        if "Submitted batch job" in out: #TODO: check if correct
            ret = out.split("Submitted batch job")[1].strip()
            return ret
        raise Exception(" Job identifier not found")

    def check_job_status(self, job_id):
        # todo: sacct -n -X -o STATE -j "28053290"
        # Remote connection
        remote = self.user + "@" + self.url
        cmd = 'sacct -n -X -o STATE -j ' + job_id
        command = [self.baseCmd, self.proxyFlag, self.proxyCmd, remote, cmd]
        process = subprocess.run(list(filter(None, command)),
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 encoding='utf8')

        ret = process.stdout.rstrip()
        if ret and ret.lower().strip() == "failed":
            # todo: nm: these failure should not return 200
            raise Exception(f"Job has failed: {job_id}")

    # Wait for a job to finish
    #TODO: change to PyCOMPSs command
    def _waitForJob(self, jobId):

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
                continue
                # raise Exception("Command '" + self.baseCmd + " " + remote + " "
                #                 + cmd + "' failed. Error: " + process.stderr)
            
            # Set a message
            self.message = process.stdout.rstrip()

            # Stop condition:
            # if the job is not in the queue, stop checking and assume that the job is finished
            if process.stdout == "":
                break
            else:
                time.sleep(60)

        # Results are available
        self.resultAvailable.set() 

class PyCOMPSsRunnerBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, **RES):
        user = RES["user"]
        url = RES["url"]
        path = RES["path"]
        if "setup" in RES.keys():
            setup = RES["setup"]           
        else:
            setup = None
        resources = RES["resources"]              
        if "proxy" in RES.keys():
            proxy = RES["proxy"]
        else:
            proxy = None
        # WARNING!!!: We dont want to do this as a Singleton
        #if not self._instance:
        #    self._instance = SlurmRunner(user, url, path)
            
        #return self._instance
        return PyCOMPSsRunner(user, url, path, resources, setup, proxy)                        
