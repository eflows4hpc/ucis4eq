#!/usr/bin/env python3
#
# RESTful server for event treatment
# This module is part of the Automatic Alert System (AAS) solution
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
import subprocess
import threading
from abc import ABC, abstractmethod

################################################################################
# Methods and classes
    
# Abstract class for defining a common interface between all workflow stages
class ScriptABC(ABC):

    #@property
    #@classmethod
    #@abstractmethod

    # Initialization method
    def __init__(self, type='slurm'):
        self.lines = []
        self.type = type
        self.time = 1
        
    # Method for defining the "buildScript" required method
    def build(self):
        raise NotImplementedError("Error: 'build' method should be implemented")

    # Just a class method for obtaining the class name
    @classmethod
    def _className(cls):
        return(cls.__name__)

    # Obtain common script header 
    def _getHeader(self):
        self.lines.append("#!/bin/bash")
        self.lines.append("")

    # Build specific slurm rules
    def _getSlurmRules(self, tlimit, nodes, tasks, cpus, qos):

        #Obtain class name
        cname = self._className()

        # Set time estimation
        self.time = tlimit

        # Add rules to the slurm script
        self.lines.append("#SBATCH --time=" + time.strftime('%H:%M:%S', time.gmtime(tlimit)))
        self.lines.append("#SBATCH --nodes=" + str(nodes))
        self.lines.append("#SBATCH --tasks-per-node=" + str(tasks))
        self.lines.append("#SBATCH --cpus-per-task=" + str(cpus))
        self.lines.append("#SBATCH --ntasks=" + str(int(nodes) * int(tasks)))
        self.lines.append("#SBATCH --error=" + cname + ".e")
        self.lines.append("#SBATCH --output=" + cname + ".o")
        self.lines.append("#SBATCH --qos=" + qos)
        self.lines.append("")
        self.lines.append("cd $SLURM_SUBMIT_DIR")

    # Generate script
    def _saveScript(self, path=""):

        # Generate the specific script
        file = path + self._className() + "." + self.type
        with open(file, 'w') as f:
            for item in self.lines:
                f.write("%s\n" % item)

        # Assign execution permisions to the script
        os.chmod(file, 0o777)
        
        return file

    # Method in charge of run and wait the script
    def run(self):

        # Build the script filename 
        script = os.path.abspath(self._className() + "." + self.type)

        # Decide how to execute the script
        if self.type == "slurm":
            Runner(self._className(), self.time).enqueueSlurm(script)
        else:
            Runner(self._className(), self.time).runBashScript(script)

        pass    

# Class in charge of running a process either Slurm or bash 
class Runner():

    # Some attributes
    message = ""
    time = 0
    task = ""
    resultAvailable = None

    # Initialization method
    def __init__(self, path, task, tlimit):
        # Task name
        self.task = task

        # Initialize the synchronizerpos
        self.resultAvailable = threading.Event()

        # Time limit
        self.time = tlimit

    # Run a bash script and return 
    def runBashScript(self, cmd):
        #print("Runnning bash script " + cmd)

        # Run the command and wait
        process = subprocess.run(cmd, stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf8')

        # Check for and error
        if process.returncode != 0:
            raise Exception("Command '" + cmd + "' failed. Error: " + process.stderr)
            pass

    # Enqueue a process and wait
    def enqueueSlurm(self, cmd):

        # Run the command and wait
        cmdm = 'sbatch ' +  cmd

        process = subprocess.run(cmdm, shell=True,
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       encoding='utf8')

        # Check for and error
        if process.returncode != 0:
            raise Exception("Command '" + cmdm + "' failed. Error: " + process.stderr)

        # Obtain the job ID
        jobId = [x.strip() for x in process.stdout.split(' ')][3]

        thread = threading.Thread(target=self._waitForSlurmJob, args=(jobId,))
        thread.start()

        # Wait for the process to finish
        #pbar = tqdm(total = self.time, position=1, leave=False)
        timeout = 5
        while not self.resultAvailable.wait(timeout=timeout):
            print('\r{}'.format(self.time), end='', flush=True)
            #pbar.set_description("STATUS: %s" % (self.message))
            #pbar.update(timeout)

        #pbar.set_description("STATUS: %s" % self.task + " completed!")
        #pbar.close()

    # Wait for a Slurm job to finish
    def _waitForSlurmJob(self, jobId):

        # Wait for the job to finish
        while True:
            # Query for the job state
            cmd = 'squeue -h -o "Slurm job %T (%M of %l)" --job ' + jobId
            process = subprocess.run(cmd, shell=True,
                                          stdout=subprocess.PIPE,
                                          stdin=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          encoding='utf8')

            # Check for and error
            if process.returncode != 0:
                raise Exception("Command '" + cmd + "' failed. Error: " + process.stderr)

            # Set a message
            self.message = process.stdout.rstrip()

            # Stop condition
            if process.stdout == "":
                break

        # Results are available
        self.resultAvailable.set()
