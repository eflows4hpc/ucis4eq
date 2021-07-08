#!/usr/bin/env python3
#
# Salvus (Wave propagation simulator)
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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module imports
# System
import sys
import os
import traceback
import json
import uuid
import yaml
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config, microServiceABC,scriptABC
import ucis4eq.dal as dal
from ucis4eq.dal import staticDataMap

################################################################################
# Methods and classes

class SalvusPrepareSubmision(scriptABC.ScriptABC):
    
    # Build the submission script
    def build(self, binary, path, args, resources, additional = []):
        # Obtain Header 
        self._getHeader()

        # Obtain Slurm rules
        r = resources
        
        # TODO: Change this depending of the target environment queue system
        self._getSlurmRules(r['wtime'], r["nodes"], r["tasks"], 
                            r["tasks-per-node"], r["qos"])

        # Additional instructions
        self.lines.append("set -e")        
        self.lines.append("module load python/3.6.1")
        for line in additional:
            self.lines.append(line)   

        # Build command
        cmd = []
        cmd.append(binary + " " + args)

        self.lines.append(" ".join(cmd))

        # Save the script to disk
        return self._saveScript(path)

@staticDataMap.build
class SalvusPrepare(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize SalvusRun instance
        """

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper
        """
        
        # Initialization
        result = {}        

        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)

        # Enable multiline writting
        yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str

        def repr_str(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
            return dumper.org_represent_str(data)

        yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)
        
        # Create the directory for the current execution
        workSpace = "/workspace/runs/" + body["trial"] + "/"
        os.makedirs(workSpace, exist_ok=True)
              
        # Write the YAML file
        inputPyaml = yaml.safe_dump(body["input"])
        pfile = workSpace + "/" + "salvus_input.yaml"
        with open(pfile, "w") as f:
           f.write(inputPyaml)

        # Prepare script's arguments
        binary = "python "  + self.filePing['salvus_wrapper']
        args = "salvus_input.yaml " + self.filePing['salvus_setup']

        # Generate Submission script
        # TODO: This is hardcoded by right now but should be parametrized
        resources = {'wtime': 1800, 'nodes': 1, 'tasks': 1, 'tasks-per-node': 1, 
                     'qos': 'debug'}
                     
        # Solver dependencies 
        additional = []
        additional.append("export PYTHON_PATH=" +\
                           os.path.dirname(self.filePing['salvus_wrapper']) +\
                           ":$PYTHON_PATH")
                                   
        script = SalvusPrepareSubmision().build(binary, workSpace, args,
                                             resources, additional)
    
        # Create the remote working directory
        rworkpath = body['trial'] + "/" + "salvus_wrapper"
        dataRepo.mkdir(rworkpath)

        # Transfer input parameter file and script
        dataRepo.uploadFile(rworkpath, script)
        dataRepo.uploadFile(rworkpath, pfile)
        
        # TODO:
        # Submit and wait for finish

        # Get the path to the Salvus input parameters
        result['salvus_input'] = dataRepo.path + "/" + rworkpath + "/salvus_input.toml"
        
        # Return list of Id of the newly created item
        return jsonify(result = result['salvus_input'], response = 201)

class SalvusRunSubmision(scriptABC.ScriptABC):
    
    # Build the submission script
    def build(self, binary, path, args, resources, additional = []):
        # Obtain Header 
        self._getHeader()

        # Obtain Slurm rules
        r = resources
        
        # TODO: Change this depending of the target environment queue system
        self._getSlurmRules(r['wtime'], r["nodes"], r["tasks"], 
                            r["tasks-per-node"], r["qos"])

        # Additional instructions
        self.lines.append("set -e")        
        self.lines.append("module load fabric")
        for line in additional:
            self.lines.append(line)
        self.lines.append("echo $SLURM_JOB_ID >> jobfile.txt")

        # Build command
        cmd = []
        cmd.append("/usr/bin/srun")
        cmd.append("--ntasks=$SLURM_NTASKS")
        cmd.append("--ntasks-per-node=$SLURM_NTASKS_PER_NODE")
        cmd.append(binary + " compute " + args)

        self.lines.append(" ".join(cmd))
        
        self.lines.append("")        
        self.lines.append("touch SUCCESS")

        # Save the script to disk
        return self._saveScript(path)

@staticDataMap.build
class SalvusRun(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize SalvusRun instance
        """

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Salvus-Compute on the remote machine
        """
        
        # Initialization
        result = {}
        
        print(body, flush=True)
        
        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)
        
        # Create the directory for the current execution
        workSpace = "/workspace/runs/" + body["trial"] + "/"
        os.makedirs(workSpace, exist_ok=True)
        
        # Obtain remote location of Salvus binary
        binary = self.filePing['salvus_compute']        
        
        # Prepare script's arguments
        args = body['input']
        
        # Generate Submission script
        # TODO: This is hardcoded by right now but should be parametrized
        resources = {'wtime': 1800, 'nodes': 1, 'tasks': 1, 'tasks-per-node': 1, 
                     'qos': 'debug'}        
        
        script = SalvusRunSubmision().build(binary, workSpace, args, resources)
    
        # Create the remote working directory
        rworkpath = body['trial'] + "/" + "salvus"
        dataRepo.mkdir(rworkpath)

        # Transfer input parameter file and script
        dataRepo.uploadFile(rworkpath, script)

        # Return list of Id of the newly created item
        return jsonify(result = workSpace + "/output", response = 201)

class SalvusPost(microServiceABC.MicroServiceABC):

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper
        """
        # Run postprocess
        os.system("/bin/bash -c 'python /root/salvusWrapper/plot_pgd_pgv_pga.py " + body["opath"] + "'")
        
        # Upload results to B2DROP
        # TODO: Select a random repository
        b2drop = dal.repositories.create('B2DROP', **dal.config)
        
        rpath = "ChEESE/PD1/Runs/" + body["uuid"] + "/"
        lpath = "/workspace/runs/" + body["uuid"] + "/"
        
        # Create remote path
        input = "/input/"
        output = "/output/"
        b2drop.mkdir(rpath)
        b2drop.mkdir(rpath + input)
        b2drop.mkdir(rpath + output)
        
        # Upload input parameters file
        file = body["uuid"] + ".yaml"
        b2drop.uploadFile(rpath + input + file, lpath + file)
        
        files = ["PGA.png", "PGD.png", "PGV.png"]
        rpath += output
        lpath += output
        for file in files:
            b2drop.uploadFile(rpath + file, lpath + file)
       
        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = {}, response = 201)
                
