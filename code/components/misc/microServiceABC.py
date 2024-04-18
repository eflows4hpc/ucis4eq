#!/usr/bin/env python3

# RESTful server for event treatment
# This module is part of the Automatic Alert System (AAS) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

# ###############################################################################
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
import sys
from abc import ABC, abstractmethod
from bson.objectid import ObjectId
from flask import jsonify
import datetime
import ucis4eq.dal as dal
import ucis4eq.misc.config as config

# ###############################################################################
# Methods and classes
class MicroServiceABC(ABC):

    # Method for defining the entry point to the service implementation
    @abstractmethod    
    def entryPoint(self, body):
        raise NotImplementedError("Error: 'entryPoint' method should be implemented")

    # Static method for decorating microservices
    @classmethod
    def runRegistration(cls, func):
        def func_wrapper(*args, **kwargs):
               # Initialize
               runInfo = {}
               status = "RUNNING"
               serviceRun = None
               className = args[0].__class__.__bases__[0].__name__
               if className == cls.__name__:
                  className = args[0].__class__.__name__

               # Check if the request provides a Dict 
               if isinstance(args[1], dict) and 'id' in args[1].keys():
                    runInfo['serviceName'] = className
                    runInfo['requestId'] = args[1]['id'] 
                    runInfo['status'] = status
                    runInfo['initTime'] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    runInfo['inputs'] = args[1]
                    if "resources" in args[1].keys():
                        runInfo['machine'] = args[1]['resources']
                    else:
                        runInfo['machine'] = "N/A"
                    serviceRun = dal.database.ServiceRuns.insert_one(runInfo).inserted_id
               else:
                    raise Exception("The 'entrypoint' method for the service '" +\
                    className + "' must define a dictionary with a 'id' key")

               # Protect a service execution
               try:
                   results = func(*args, **kwargs)
                   status = "SUCCESS"
               except Exception as e:
                   config.printException()
                   status = "FAILED"
                   if runInfo.keys():
                       dal.database.Requests.update_one(
                            {'_id': ObjectId(runInfo['requestId'])},
                            {'$set': {"state": status}})

                   # Return error code and message
                   results = jsonify(result = str(e), response = 501)

               try:
                   dal.database.ServiceRuns.update_one({'_id': ObjectId(serviceRun)},
                   {'$set': {"endTime": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), 
                   "status": status}})
               except Exception as e:
                   config.printException()

               return results
        return func_wrapper
