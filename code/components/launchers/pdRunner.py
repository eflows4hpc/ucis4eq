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

        # Add rules to the slurm script
        lines.append("#SBATCH --job-name=" + stage)
        lines.append("#SBATCH --time=" + time.strftime('%H:%M:%S', time.gmtime(args['tlimit'])))
        lines.append("#SBATCH --tasks-per-node=" + str(args['tasks']))
        lines.append("#SBATCH --ntasks=" + str(int(args['nodes']) * int(args['tasks'])))
        lines.append("#SBATCH --error=" + args['cname'] + ".e")
        lines.append("#SBATCH --output=" + args['cname'] + ".o")
        lines.append("#SBATCH --partition=" + args['partition'])
        lines.append("#SBATCH --constraint=" + args['constraint'])
        lines.append("#SBATCH --account=" + args['account'])

        lines.append("")
        lines.append("cd $SLURM_SUBMIT_DIR")
        lines.append("")        
        
        # Return the set of instructions
        return lines

    # Method for obtaining environment setup (module loads, PATH, conda environmnet, etc ...)
    def getEnvironmentSetup(self):
        # Initialize list of instructions
        lines = []
        
        # Piz Daint MPI setup
        lines.append("export LD_LIBRARY_PATH=/opt/cray/pe/mpt/7.7.15/gni/mpich-gnu-abi/8.2/lib:$LD_LIBRARY_PATH")
        lines.append("export CRAY_CUDA_MPS=1")
        
        # Additional instructions
        lines.append("set -e")

        # Enabling Singulatity
        lines.append("module load singularity")
        
        # Enabling Cheese environment (that includes Salvus)
        lines.append("source activate cheese")
                
        # Enabling Cheese environment (that includes Salvus)
        lines.append("module switch PrgEnv-cray PrgEnv-gnu")
        lines.append("module switch cray-mpich cray-mpich-abi")

        return lines        
    
class PDRunnerBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, DAINT, **_ignored):
        user = DAINT["user"]
        url = DAINT["url"]
        path = DAINT["path"]
        resources = DAINT["resources"]           
        proxy = DAINT["proxy"]
        # WARNING!!!: We dont want to do this as a Singleton
        #if not self._instance:
        #    self._instance = SlurmRunner(user, url, path)
            
        #return self._instance
        return PDSlurmRunner(user, url, path, resources, proxy)
