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
from ucis4eq.misc import config, microServiceABC
from ucis4eq.launchers import scriptABC
import ucis4eq.dal as dal
import ucis4eq as ucis4eq
from ucis4eq.dal import staticDataMap

################################################################################
# Methods and classes

class SalvusWrapperSubmision(scriptABC.ScriptABC):
    
    # Build the submission script
    def build(self, commands, path, resources, additional = []):
        # Obtain Header 
        self._getHeader()

        # Obtain Slurm rules
        r = resources
        
        # TODO: Change this depending of the target environment queue system
        self._getRules(r['wtime'], r["nodes"], r["tasks-per-node"], 
                            r["cpus-per-task"], r["qos"])

        # Additional instructions
        self.lines.append("set -e")        
        
        # TODO: Add those specific directives onto the proper resource 
        #       definition (JSON).
        self.lines.append("module load ANACONDA/5.0.1")
        self.lines.append("source activate cheese")
        
        for line in additional:
            self.lines.append(line)

        # Build command
        for command in commands:
            self.lines.append("")
            self.lines.append(command[0] + " " + command[1])


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
    @microServiceABC.MicroServiceABC.runRegistration                
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper
        """
        
        # Initialization
        result = {}        
        
        # Select target machine
        machine = body['resources']        

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
        commands = []        
        binary = "python "  + self.filePing['salvus_wrapper']
        args = "--ucis4eq salvus_input.yaml " +\
               "--salvus " + self.filePing['salvus_setup']
               
        commands.append((binary, args)) 
        
        # Generate Submission script
        # TODO: This is hardcoded by now but should be parametrized
        resources = {'wtime': 1800, 'nodes': 1, 'tasks-per-node': 1,
                     'cpus-per-task': 48, 'qos': 'debug'}
                     
        # Solver dependencies 
        additional = []
        additional.append("export PYTHONPATH=" +\
                           os.path.dirname(self.filePing['salvus_wrapper']) +\
                           ":$PYTHONPATH")
            
        
        # Submission instance   
        submission = SalvusWrapperSubmision(machine)
        
        script = submission.build(commands, workSpace, resources, additional)
    
        # Create the remote working directory
        rworkpath = body['trial'] + "/" + "salvus_wrapper"
        dataRepo.mkdir(rworkpath)

        # Transfer input parameter file and script
        dataRepo.uploadFile(rworkpath, script)
        dataRepo.uploadFile(rworkpath, pfile)
        
        # Submit and wait for finish
        submission.run(dataRepo.path + "/" + rworkpath)

        # Get the path to the Salvus input parameters
        result['salvus_input'] = dataRepo.path + "/" + rworkpath + "/salvus_input_rupture.toml"
        
        # Return list of Id of the newly created item
        return jsonify(result = result['salvus_input'], response = 201)

class SalvusRunSubmision(scriptABC.ScriptABC):
    
    # Build the submission script
    def build(self, commands, path, resources, additional = []):
        # Obtain Header 
        self._getHeader()

        # Obtain Slurm rules
        r = resources
        
        # TODO: Change this depending of the target environment queue system
        self._getRules(r['wtime'], r["nodes"], r["tasks-per-node"], 
                            r["cpus-per-task"], r["qos"])

        # Additional instructions
        self.lines.append("set -e")
        
        self.lines.append("module load ANACONDA/5.0.1")
        self.lines.append("source activate cheese")
                
        self.lines.append("module load fabric")
        self.lines.append("export I_MPI_EXTRA_FILESYSTEM_LIST=gpfs")
        self.lines.append("export I_MPI_EXTRA_FILESYSTEM=on")
        
        for line in additional:
            self.lines.append(line)
        self.lines.append("echo $SLURM_JOB_ID >> jobfile.txt")

        # Build command
        for command in commands:
            self.lines.append("")
            self.lines.append(command[0] + " " + command[1])
        
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
    @microServiceABC.MicroServiceABC.runRegistration    
    def entryPoint(self, body):
        """
        Call the Salvus-Compute on the remote machine
        """
        
        # Initialization
        result = {}
        
        # Select target machinefgetRules
        machine = body['resources']
                
        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)
        
        # Create the directory for the current execution
        workSpace = "/workspace/runs/" + body["trial"] + "/"
        os.makedirs(workSpace, exist_ok=True)
        
        # Obtain remote location of Salvus binary
        binary = self.filePing['salvus_compute']
        
        # Prepare script's arguments 
        commands = []
        
        # ... build command for job monitoring
        binary = "python "  + self.filePing['salvus_job_tracker']
        args = body['input'] + " $PWD 10 snapshots &"
        commands.append((binary, args))
        
        # ... build command for the modeling
        binary = "/usr/bin/srun --ntasks=$SLURM_NTASKS --ntasks-per-node=$SLURM_NTASKS_PER_NODE " +\
                  self.filePing['salvus_compute'] + " compute "
        args = body['input']
        commands.append((binary, args))
        
        # Generate Submission script
        # TODO: This is hardcoded by right now but should be parametrized
        resources = {'wtime': 2400, 'nodes': 10, 'tasks-per-node': 48,
                     'cpus-per-task': 1, 'qos': 'debug'}
        
        # Submission instance   
        submission = SalvusRunSubmision(machine)
        
        script = submission.build(commands, workSpace, resources, [])
    
        # Create the remote working directory
        rworkpath = body['trial'] + "/" + "salvus"
        dataRepo.mkdir(rworkpath)

        # Transfer input parameter file and script
        dataRepo.uploadFile(rworkpath, script)
        
        # Submit and wait for finish
        submission.run(dataRepo.path + "/" + rworkpath)

        # Return list of Id of the newly created item
        return jsonify(result = workSpace, response = 201)
    
@staticDataMap.build
class SalvusPost(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """

        # Select the database
        self.db = ucis4eq.dal.database

    # Service's entry point definition
    @config.safeRun
    @microServiceABC.MicroServiceABC.runRegistration    
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper (Postprocessing scripts)
        """
        
        # Obtain the domain in DB
        domain = self.db["Domains"].find_one({"id": body['domain']['id']})

        # Prepare the input parameters file
        inputP = {}
        inputP['fmax_in_hz'] = domain['parameters']['freq_max']
        inputP['geometry'] = {'coordinates': domain['model']['geometry']}
        
        # Initialization
        result = {}
        
        # Select target machinefgetRules
        # TODO Do this in a clever way!
        machine = body['resources']        

        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)        
        
        # Create the directory for the current execution
        bpath = body['base'] + "/" + body['domain']['id'] + "/"
        workSpace = "/workspace/runs/" + bpath
        os.makedirs(workSpace, exist_ok=True)       
        
        # Write the YAML file
        inputPyaml = yaml.safe_dump(inputP)
        pfile = workSpace + "/" + "salvus_input.yaml"
        with open(pfile, "w") as f:
           f.write(inputPyaml)
        
        pattern = "/trial_" + body['domain']['id'] + "*/"
        root = dataRepo.path + "/"
        pworkpath = root + bpath + "/" + "salvus_post/"
        wworkpath = root + body["trial"] +  "/" + "salvus_wrapper/"        
        sworkpath = root + body['base'] + pattern + "salvus/"
        
        # Prepare script's arguments
        commands = []
        # ... for postprocessing
        binary = "python "  + self.filePing['salvus_wrapper_post']
        args = "--ucis4eq " + pworkpath + "salvus_input.yaml " +\
               "--salvus "  + self.filePing['salvus_setup'] + " " +\
               "--coordsdata " +  wworkpath + " " +\
               "--rawdata " + sworkpath
        commands.append((binary, args))
        
        # ... and plotting
        binary = "python "  + self.filePing['salvus_wrapper_plot']
        args = "--processeddata " + sworkpath + " " +\
               "--topogrid " + self.filePing["SamosIzmir_grid_topo"]
        commands.append((binary, args))
        
        # ... move to proper directory
        binary = "cd"
        args = pworkpath
        commands.append((binary, args))
        
        # ... create symbolic link
        binary = "ln"
        args = "-s " + root + body['base'] + " " + body['base']
        commands.append((binary, args))
        
        # ... create symbolic link
        binary = "tar "
        args = "czvf  " + body['base'] + ".tar.gz " + body['base'] +\
                pattern + "salvus/*.png"
        commands.append((binary, args))
        
        # ... create symbolic link
        binary = "rm  "
        args = "-fr " + body['base']
        commands.append((binary, args))           
        
        # Generate Submission script
        # TODO: This is hardcoded by now but should be parametrized
        resources = {'wtime': 1800, 'nodes': 1, 'tasks-per-node': 1,
                     'cpus-per-task': 48, 'qos': 'debug'}        
        
        # Solver dependencies 
        additional = []
        additional.append("export PYTHONPATH=" +\
                           os.path.dirname(self.filePing['salvus_wrapper_post']) +\
                           ":$PYTHONPATH")
                           
        # Submission instance   
        submission = SalvusWrapperSubmision(machine)     
        
        script = submission.build(commands, workSpace, resources, additional)        
                              
        # Create the remote working directory
        rworkpath = bpath + "salvus_post"
        dataRepo.mkdir(rworkpath)

        # Transfer input parameter file and script
        dataRepo.uploadFile(rworkpath, script) 
        dataRepo.uploadFile(rworkpath, pfile)        
        
        # Submit and wait for finish
        submission.run(dataRepo.path + "/" + rworkpath)
        
        # Return list of Id of the newly created item
        #return jsonify(result = {}, response = 201)
        
        # Download results from HPC machine
        dataRepo.downloadFile(rworkpath + "/" + body['base'] + ".tar.gz", 
                              workSpace + body['base'] + ".tar.gz")
    
        # Upload results to B2DROP
        # TODO: Select a random repository
        b2drop = dal.repositories.create('B2DROP', **dal.config)
        
        rpath = "ChEESE/PD1/Runs/" + body["base"] + "_" + body['domain']['id']  + "/"
        lpath = workSpace
        
        ## Create remote path
        #input = "/input/"
        #b2drop.mkdir(rpath + input)
        b2drop.mkdir(rpath)

        # Upload results        
        file = body['base'] + ".tar.gz"
        b2drop.uploadFile(rpath + file, lpath + file)
        
        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = {}, response = 201)
                
class SalvusPing(microServiceABC.MicroServiceABC):

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
        progress = {}
        
        # Select target machinefgetRules
        machine = body['resources']
                
        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)
        
        # Create the directory for the current execution
        workSpace = "/workspace/runs/" + body["trial"] + "/"
        os.makedirs(workSpace, exist_ok=True)
        
        # Create the remote working directory
        filename = "progress.json"  
        rfile = body['trial'] + "/salvus/" + filename
        lfile = workSpace + filename

        # Download results from HPC machine
        dataRepo.downloadFile(rfile, lfile)
    
        # Read local json file
        with open(lfile, 'r') as f:
            progress = json.load(f)

        # Return list of Id of the newly created item
        return jsonify(result = progress, response = 201)
