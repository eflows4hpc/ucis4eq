#!/usr/bin/env python3
#
# RESTful server for event treatment
# This module is part of the Automatic Alert System (AAS) solution
#
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
import threading
from abc import ABC, abstractmethod

import ucis4eq.launchers as launchers

################################################################################
# Methods and classes
    
# Abstract class for defining a common interface between all workflow stages
class ScriptABC(ABC):

    #@property
    #@classmethod
    #@abstractmethod

    # Initialization method
    def __init__(self, type='LOCAL'):
        self.lines = []
        self.type = type
        self.time = 1
        
        # Create the specific launcher 
        self.launcher = launchers.launchers.create(type, **launchers.config)
        
        # Obtain the script's filename
        self.fileName = self._className() + "." + self.type + "." + self.launcher.type        
        
    # Method for defining the "buildScript" required method
    @abstractmethod        
    def build(self):
        raise NotImplementedError("Error: 'build' method should be implemented")

    # Method for defining the "buildScript" required method
    def getMPICommand(self):
        return self.launcher.getMPICommand()

    # Just a class method for obtaining the class name
    @classmethod
    def _className(cls):
        return(cls.__name__)

    # Obtain common script header 
    def _getHeader(self):
        self.lines.append("#!/bin/bash")
        self.lines.append("")

    # Build specific slurm rules
    def _getRules(self, stage):

        self.lines = self.lines \
                     + self.launcher.getRules(stage) \
                     + self.launcher.getEnvironmentSetup(stage)
                     
        self.lines.append("")                                                                                      

    # Generate script
    def _saveScript(self, path=""):

        # Generate the specific script
        file = path + self.fileName
        with open(file, 'w') as f:
            for item in self.lines:
                f.write("%s\n" % item)

        # Assign execution permisions to the script
        os.chmod(file, 0o777)
        
        return file

    # Method in charge of run and wait the script
    def run(self, path):

        # Build the script filename 
        script = path + '/' + self.fileName

        # Launch and wait for results
        self.launcher.run(path, script)
