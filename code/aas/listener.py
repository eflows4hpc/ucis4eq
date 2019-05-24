#!/usr/bin/env python3                                                                                                                                                                                                                         
#
# FDSN-WebService Listener
# This module is part of the Automatic Alert System (AAS) solution
# 
# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bself.es, josep.delapuente@bself.es
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
import uuid 
import io
import sys
import traceback
import argparse
import json
import requests
import sched, time
import multiprocessing
import obspy
import datetime

################################################################################
# Methods and classes

# Interface class 
class WSGeneral:

    
    # Methos
    def __init__(self, config):
        # Object UUID
        #self.uuid = uuid.uuid1()
        
        # Store the configuration parameters 
        self.config = config
        
        # Attributes
        self.results = {}
        
        # Create the recursive scheduler
        self.s = sched.scheduler(time.time, time.sleep)
        
        # Config such scheduler
        self.s.enter(0, 1, self.exploreRepositories, ())
        
        # Start the AAS service
        self.s.run()
    
    # Explore the set of input repositories    
    def exploreRepositories(self, pool = None):
        # Prepare the pool of processes
        np = len(self.config['repositories'])
        
        ws = self.config['webservice']
        output = {}
        
        #print("Creating pool with", str(np), "processes")
        
        # Create the processes pool just one
        if not pool:
            pool = multiprocessing.Pool(np)
        
        query = ws['interface'] + "/" + ws['majorversion'] + "/"
        query = query + ws["application"] + "?"
        for p in ws["parameters"]:
            query = query + p + "=" + ws["parameters"][p]+"&"
        
        query = query.strip('&')
        
        # Create the file name 
            
        # For each provided repository
        tasks = [(self.requestRepository, 
                 (r['name'],
                  r['url']+query)) for r in self.config['repositories']]
        imap_unordered_it = pool.imap_unordered(self.runtask, tasks)
        
        # Wait the tasks to finish
        for name, result in imap_unordered_it:
            self.results[name] = result
                
        # Store the current timestamp
        self.postprocess_actions()
        
        # Generate JSON file containing the generated metada
        for r in self.config['repositories']:
            repo = {}
            repo['url'] = r['url']+query
            repo['data'] = r['name']+self.config['listener']['data_ext']
            output[r['name']] = repo

        with open(self.config['listener']['results_name'], "w") as f:
            json.dump(output, f, indent=4)
        
        # Start running the triggering system
        #os.system(self.config['listener']['trigger'] + "&")
        
        # Queue the following job
        interval = self.config['listener']['interval']
        if( interval > 0 ):
            #print("Next report in ", interval, "seconds")
            self.s.enter(interval, 1, self.exploreRepositories, kwargs={'pool': pool})
        
    # Do the REST-GET petition
    def requestRepository(self, name, url):
        # Request data
        #print("Requesting info from '" + url + "'")
        self.r = requests.get(url, stream=True)
                
        # Process data
        return (name, self.process_data(self.r, name))
            
    # Process obtained data
    def process_data(self, results, name):
        # Write file to disk
        with open(name+self.config['listener']['data_ext'], 'wb') as f:
            f.write(results.content)
            
    # Post-process actions
    def postprocess_actions(self):
        pass
            
    # For parallel computing    
    def __execute(self,func, args):
        result = func(*args)
        return result

    def runtask(self, args):
        return self.__execute(*args)
        
class WSEvents(WSGeneral):
    
    def __init__(self, config):
        # Attributes
        self.currenttime = None
        
        #WSGeneral.__init__(self,config)
        super(WSEvents, self).__init__(config)
        #self.uuid = uuid.uuid1()
    
    def process_data(self, results, name):
        # Variables 
        params = self.config['webservice']['parameters']
        
        # Write the original file to disk
        super(WSEvents, self).process_data(results, name)
            
        # Check the requested format 
        if( 'format' in params.keys() and params['format'] == "xml"):
            return self.process_xml_data(results, name)
        
        return 0
            
    # Process a QuakeML data
    def process_xml_data(self, results, name):
        # Variables
        now = None
        delay = None
        cat = None
        
        # Set the time threshold 
        if( name in self.results.keys() ):
            currenttime = self.results[name]
        else:
            currenttime = 0.0
        
        try:
            # Read the set of events
            cat = obspy.read_events(name+self.config['listener']['data_ext'], "QUAKEML")
        except Exception as error:
            #print("Obspy error", error )
            return 0
        
        #print(name, ":", self.a)
        #self.a = cat.count()
        #print("[", name, "] --> ", cat.count(),"events found")
            
        for e in cat:
            if( currenttime < e.origins[0]['time'].timestamp ):
                now = datetime.datetime.now(datetime.timezone.utc)
                delay = now.timestamp() - e.origins[0]['time'].timestamp
                print(now,
                    "[", name, "] --> ",  e.origins[0]['time'].datetime, 
                    e.origins[0]['latitude'], e.origins[0]['longitude'], 
                    e.origins[0]['depth'], e.magnitudes[0]['mag'],
                    "Delay (secs):", delay)
                # TODO Do something here!
                    
        #print(name, ":", self.a)
        #print( cat.__str__(print_all=True) )
        #print("[", name, "] --> ",  cat[0].origins[0]['time'], 
        #    cat[0].origins[0]['latitude'], cat[0].origins[0]['longitude'], 
        #    cat[0].origins[0]['depth'], cat[0].magnitudes[0]['mag'])
            #self.currenttime = cat[1]['creation_info']['creation_time']
        return cat[0].origins[0]['time'].timestamp
    
    # Post-process actions
    def postprocess_actions(self):
        #self.currenttime = time.time()
        pass

def format_ts(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                
# Arguments parser
def parser():
    
    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='listener',
        description='FDSN-WS Listener')
    parser.add_argument('config', help='JSON configuration file')
    args = parser.parse_args()
    
    # Check the arguments
    if not os.path.isfile(args.config):
      raise Exception("The configuration file '"+args.config+ "' doesn't exist")
    
    # Return them
    return args

# Main Method
def main():
    try:    
        # Call the parser
        args = parser()
                
        # Read the configuration file
        with open(args.config, 'r') as f:
            config = json.load(f)
            
        if( config['webservice']['interface'] == "event" ):
            ws = WSEvents(config)
        else:
            ws = WSGeneral(config)
        
    except Exception as error:
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)

################################################################################
# Run the program
if __name__ == "__main__": 
    main()
