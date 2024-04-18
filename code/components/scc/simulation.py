#!/usr/bin/env python3

# Execution of the simulation workflows

# Author:  Jorge Ejarque Artigas
# Contact: jorge.ejarque@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2024, Jorge Ejarque Artigas

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
# System
import sys
import os
import traceback
import json
import uuid
import random
import yaml
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
import ucis4eq
import ucis4eq.dal as dal
from ucis4eq.misc import config, microServiceABC
from ucis4eq.launchers.scriptABC import ScriptABC
from ucis4eq.dal import staticDataMap, staticDataAccess, dataStructure

import ucis4eq.launchers as launchers

# ###############################################################################
# Methods and classes

class SimulationSubmision(ScriptABC):

    # Initialization method
    def __init__(self, resource):
        self.lines = []
        self.type = resource["id"]
        self.time = 1

        conf = launchers.config[self.type]
        conf.update(resource)
        # Create a launcher to obtain the Setup
        launcher = launchers.launchers.create(self.type, **conf)
        self.launcher = launcher

        # Obtain the script's filename
        self.fileName = self._className() + "." + self.type + "." + self.launcher.type


        # Build the submission script
    def build(self, path, args, stage):

        # Obtain Header
        self._getHeader()

        # Obtain Enqueue_command
        cmd = self.launcher.getRules(stage)
        cmd.append(args)

        self.lines = self.lines + self.launcher.getEnvironmentSetup(stage)

        self.lines.append("")
        self.lines.append(" ".join(cmd))

        # Additional instructions
        self.lines.append("")
        print(f"writing to {path} : \n {self.lines}")

        # Save the script to disk
        return self._saveScript(path)



@staticDataMap.build
class SimulationRun(microServiceABC.MicroServiceABC):

    # Mai-Beroza relations
    def _MaiBerozaRelations(self, mw, lat, lon, depth):

        log_Mo = (mw*1.5)+9.05

        relations = {}

        relations['FAULT_LENGTH'] = 10**(-6.13 + (0.39*log_Mo)) #32.84
        relations['FAULT_WIDTH'] =  10**(-5.05 + (0.32*log_Mo)) #27.8
        relations['DEPTH_TO_TOP'] =  depth/1000 - (relations['FAULT_WIDTH']/2) #10.666
        relations['LAT_TOP_CENTER'] = lat
        relations['LON_TOP_CENTER'] = lon
        relations['HYPO_ALONG_STK'] = 0.0 #-2.72
        relations['HYPO_DOWN_DIP'] = relations['FAULT_WIDTH']/2 #16.24

        return relations
    
    def _SeisEnsManRelations(self, mw, lat, lon, depth, length, area):


        relations = {}

        relations['FAULT_LENGTH'] = float(length)
        relations['FAULT_WIDTH'] =  float(area)/relations['FAULT_LENGTH']

        if float(depth) < relations['FAULT_WIDTH']/2:
            relations['DEPTH_TO_TOP'] =  0
            relations['HYPO_DOWN_DIP'] =  float(depth)
        else:
            relations['DEPTH_TO_TOP'] = float(depth) - (relations['FAULT_WIDTH']/2)
            relations['HYPO_DOWN_DIP'] = relations['FAULT_WIDTH']/2

        relations['LAT_TOP_CENTER'] = float(lat)
        relations['LON_TOP_CENTER'] = float(lon)
        relations['HYPO_ALONG_STK'] = 0.0

        return relations

    def create_rupture_inputs(self, path, remote_path, body):
        cmt = body['CMT']
        event = body['event']
        setup = body['setup']

        source = path +"/inputs.src"
        remote_source = remote_path + "/inputs.src"
        # Generate GP source file
        if body['ensemble'] == "statisticalCMT":
            srcParams = self._MaiBerozaRelations(event['magnitude'],
                                                 event['latitude'],
                                                 event['longitude'],
                                                 event['depth'])
            srcParams['MAGNITUDE'] = event['magnitude']
            srcParams['STRIKE'] = cmt['strike']
            srcParams['RAKE'] = cmt['rake']
            srcParams['DIP'] = cmt['dip']
            setup = body['setup']
            srcParams['DWID'] = setup['dwid']
            srcParams['DLEN'] = setup['dlen']
            srcParams['CORNER_FREQ'] = setup['corner_freq']

        elif body['ensemble'] == "seisEnsMan":
            srcParams = self._SeisEnsManRelations(cmt['magnitude'],
                                                  cmt['latitude'],
                                                  cmt['longitude'],
                                                  cmt['depth'],
                                                  cmt['faultLength'],
                                                  cmt['faultArea'])
            srcParams['MAGNITUDE'] = cmt['magnitude']
            srcParams['STRIKE'] = cmt['strike']
            srcParams['RAKE'] = cmt['rake']
            srcParams['DIP'] = cmt['dip']
            setup = body['setup']
            srcParams['DWID'] = setup['dwid']
            srcParams['DLEN'] = setup['dlen']
            srcParams['CORNER_FREQ'] = setup['corner_freq']
        else:
            raise Exception('Not recognized ensemble')

        if 'seed' in body.keys():
            srcParams['SEED'] =  body['seed']
        else:
            srcParams['SEED'] =  random.randint(1, 9999999)

        with open(source, 'w') as fd:
            for key in srcParams.keys():
                fd.write(key + ' = ' + str(srcParams[key]) + '\n')
        return source, remote_source

    def _create_salvus_input_yml(self, path, remote_path, body):
        # Write the YAML file
        inputPyaml = yaml.safe_dump(body["input"])
        pfile = path + "/salvus_input.yaml"
        remote_file = remote_path + "/salvus_input.yaml"
        with open(pfile, "w") as f:
           f.write(inputPyaml)
        return pfile, remote_file

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Call the Submission
        """
        # Initialization
        result = {}

        # Select target machine
        machine = body['resources']

        # Set repository
        self.setMainRepository(machine['repository'])

        # Create the data structure
        dataFormat = dataStructure.formats[body['region']['file_structure']]()
        dataFormat.prepare(body['region']['id'])

        # Creating the repository instance for data transfer    
        dataRepo = staticDataAccess.repositories.create(machine['repository'], **dal.config)

        # Create local directories
        path =  ucis4eq.workSpace + "/scratch/outdata/" + body['trial'] + "/"
        workSpace = "/workspace/runs/" + body["trial"] + "/"
        os.makedirs(workSpace, exist_ok=True)
        os.makedirs(path, exist_ok=True)

        cmt = body['CMT']
        event = body['event']
        setup = body['setup']
        slip_id = body['trial']

        remote_workflow_path = self.filePing["simulation_workflow"]
        remote_working_path = slip_id + "/"
        remote_exec_dir = dataRepo.path + "/" + remote_working_path

        # Define Source file and Generate GP source file
        source, remote_source = self.create_rupture_inputs(path, remote_exec_dir, body)
        # Define and Generate salvus input
        input_yaml, remote_input_yaml = self._create_salvus_input_yml(workSpace, remote_exec_dir, body)
        remote_region_file = remote_exec_dir + "/" + setup['model']

        # todo: nm: remove --keep_workingdir
        args =  "--keep_workingdir --job_execution_dir=" + remote_exec_dir + " --log_dir=" + remote_exec_dir + \
            " --worker_working_dir=" + remote_exec_dir + " " + remote_workflow_path +"/hpc_workflow.py" + \
            " --slip_id " + slip_id + " --salvus_input " + remote_input_yaml + " --slip_src " + remote_source + \
            " --salvus_setup " +self.filePing['salvus_setup'] + " --region "+ remote_region_file + " --dt " + str(setup['dt'])
        # Prepare script's arguments
        initSlip = ""
        if "initSlip" in cmt.keys():
            initSlip = " -i " + \
                        os.path.basename(self.fileMapping[cmt['initSlip']]) \
                        + " -a 0.9"

        #args = "-o " + result['id'] + " -v " + self.fileMapping[setup['model']] + " -s " + source + " -i " + self.fileMapping["initSlip21june2000"] + " -a 0.99 > /dev/null 2>&1"

        # Submission instance   
        submission = SimulationSubmision(machine)

        script = submission.build(path, args, "SimulationRun")

        # Create the remote working directory 
        dataRepo.mkdir(remote_working_path)

        # Transfer source, script, model and init slip (if there is one)
        dataRepo.uploadFile(remote_working_path, script)
        dataRepo.uploadFile(remote_working_path, source)
        dataRepo.uploadFile(remote_working_path, input_yaml)
        if "initSlip" in cmt.keys():
            dataRepo.uploadFile(remote_working_path, self.fileMapping[cmt['initSlip']])

        modelFileName = setup['path'] + "/" + \
                        dataFormat.getPathTo('slip_gen') + "/" + \
                        setup['model']

        dataRepo.uploadFile(remote_working_path, modelFileName)
        
        # Submit and wait for finish
        submission.run(remote_exec_dir)

        return jsonify(result = result, response = 201)


@staticDataMap.build
class SimulationPostSwarm(microServiceABC.MicroServiceABC):

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
        Call the Simulation Post Workflow (Postprocessing scripts)
        """

        # Initialization
        result = None

        # Select target machinef
        machine = body['resources']

        # Set repository
        self.setMainRepository(machine['repository'])

        # Creating the repository instance for data transfer    
        dataRepo = staticDataAccess.repositories.create(machine['repository'], **dal.config)

           # Create the data structure
        regionName = body['region']['id'] + "_DATA"
        dformat =  body['region']['file_structure']
        dataFormat = dataStructure.formats[dformat]()
        dataFormat.setMainRepository(machine['repository'])
        dataFormat.prepare(regionName)

        # Create the directory for the current execution
        bpath = body['base'] + "/"
        workSpace = "/workspace/runs/" + bpath
        os.makedirs(workSpace, exist_ok=True)

        # this asterisk is a problem
        pattern = "\"/trial_" + "*/salvus_post/\""
        remote_workflow_path = self.filePing['simulation_workflow']
        remote_working_path = body['base'] + "/"
        remote_exec_dir = dataRepo.path + "/" + remote_working_path
        processed_data = remote_exec_dir + pattern

        args =  "--keep_workingdir --job_execution_dir=" + remote_exec_dir + " --log_dir=" + remote_exec_dir + \
            " --worker_working_dir=" + remote_exec_dir + " " + remote_workflow_path + "/hpc_post_process.py" + \
            " -e " + remote_exec_dir + " --processeddata " + processed_data +" --output " + remote_exec_dir

        topogrid = dataFormat.getPathTo('topography', ["grid"])

        if topogrid:
               args = args + " --topogrid " + topogrid

        # Submission instance   
        submission = SimulationSubmision(machine)

        script = submission.build(workSpace, args, "SimulationPost")

        # Create the remote working directory 
        dataRepo.mkdir(remote_working_path)

        # Transfer input parameter file and script
        dataRepo.uploadFile(remote_working_path, script)

        # Submit and wait for finish
        submission.run(remote_exec_dir)

        # Download results from HPC machine
        local_tar = body['base'] + ".tar.gz"
        print(remote_working_path + "/" + body['base'] + ".tar.gz")
        print(local_tar)
        # todo: nm: make this salvus_plot path parametric
        dataRepo.downloadFile(remote_working_path + "/salvus_plot/" + body['base'] + ".tar.gz",
                              local_tar)

        # Upload results to B2DROP
        b2drop = staticDataAccess.repositories.create(dal.repository, **dal.config)
        outputPath = dal.config[dal.repository]["output"]

        rpath = outputPath + "/" + body["base"] + "_" + body['region']['id']  + "/"
        lpath = workSpace

        ## Create remote path
        #input = "/input/"
        #b2drop.mkdir(rpath + input)
        b2drop.mkdir(rpath)

        # Upload results        
        file = body['base'] + ".tar.gz"
        b2drop.uploadFile(rpath + file, local_tar)

        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = result, response = 201)

