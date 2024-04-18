#!/usr/bin/env python3

# Slurm specialization launcher
# This module is part of the Smart Center Control (SSC) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Josep de la Puente, Juan Esteban Rodriguez
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
import uuid
import subprocess
import threading

from ucis4eq.launchers.slurmRunnerABC import SlurmRunnerABC

################################################################################
# Methods and classes

class PDSlurmRunner(SlurmRunnerABC):
            
    # Obtain the spefific rules for a slurm Script    
    def getRules(self, stage):
        
        # Initialize list of instructions
        lines = []
        
        # Select the resources for the given stage
        # TODO: Control that provided stage exist
        args = self.resources[stage]        
        
        # Check if a job name was provided
        if "name" in args.keys():
            name = args['name']
        else:
            name = stage        
        
        # Add rules to the slurm script
        lines.append("#SBATCH --job-name=" + name)
        lines.append("#SBATCH --time=" + time.strftime('%H:%M:%S', time.gmtime(args['wtime'])))
        lines.append("#SBATCH --tasks-per-node=" + str(args['tasks-per-node']))
        lines.append("#SBATCH --ntasks=" + str(int(args['nodes']) * int(args['tasks-per-node'])))
        lines.append("#SBATCH --error=" + stage + ".e")
        lines.append("#SBATCH --output=" + stage + ".o")
        lines.append("#SBATCH --partition=" + args['partition'])
        lines.append("#SBATCH --constraint=" + args['constraint'])
        lines.append("#SBATCH --account=" + args['account'])

        lines.append("")
        lines.append("cd $SLURM_SUBMIT_DIR")
        lines.append("")        
        
        # Return the set of instructions
        return lines

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
    
class PDRunnerBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, DAINT, **_ignored):
        user = DAINT["user"]
        url = DAINT["url"]
        path = DAINT["path"]
        if "setup" in DAINT.keys():
            setup = DAINT["setup"]           
        else:
            setup = None
        resources = DAINT["resources"]              
        proxy = DAINT["proxy"]
        # WARNING!!!: We dont want to do this as a Singleton
        #if not self._instance:
        #    self._instance = SlurmRunner(user, url, path)
            
        #return self._instance
        return PDSlurmRunner(user, url, path, resources, setup, proxy)
