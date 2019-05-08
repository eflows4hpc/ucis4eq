#!/usr/bin/env python3                                                                                                                                                                                                                         
#
# FDSN-WebService Listener
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
import sys
import traceback
import argparse
import json
import requests
import sched, time
import multiprocessing

################################################################################
# Methods and classes

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
    
def calculate(func, args):
    result = func(*args)
    return '%s says that %s%s = %s' % (
        multiprocessing.current_process().name,
        func.__name__, args, result
        )

def calculatestar(args):
    return calculate(*args)    
    
def requestRepository(name, url):
    # Request data
    print("Requesting info from '" + url + "'")
    r = requests.get(url)

    # Write file to disk
    f = open(name, 'w')
    f.write(r.text)
    f.close()
    
def exploreRepositories(sc, pool = None):
    
    # Prepare the pool of processes
    np = len(sc.config['repositories'])
    
    ws = sc.config['webservice']
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
    tasks = [(requestRepository, 
             (r['name']+sc.config['listener']['data_ext'],
              r['url']+query)) for r in sc.config['repositories']]
    imap_unordered_it = pool.imap_unordered(calculatestar, tasks)
    
    # Generate JSON file containing the generated metada
    for r in sc.config['repositories']:
        repo = {}
        repo['url'] = r['url']+query
        repo['data'] = r['name']+sc.config['listener']['data_ext']
        output[r['name']] = repo

    
    with open(sc.config['listener']['results_name'], "w") as f:
        json.dump(output, f, indent=4)
    
    # Start running the triggering system
    os.system(sc.config['listener']['trigger'] + "&")
    
    # Queue the following job
    sc.enter(sc.config['listener']['interval'], 1, exploreRepositories, (sc, pool))

# Main Method
def main():
    try:
        # Call the parser
        args = parser()
        
        # Create the recursive scheduler
        s = sched.scheduler(time.time, time.sleep)
        
        # Read the configuration file
        with open(args.config, 'r') as f:
            s.config = json.load(f)
                
        
        # Config such scheduler
        
        s.enter(0, 1, exploreRepositories, (s,))

        # Start the AAS service
        s.run()
        
    except Exception as error:
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)

################################################################################
# Run the program
if __name__ == "__main__": 
    main()
