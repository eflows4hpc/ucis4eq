#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
import random
import numpy as np

from haversine import haversine

import obspy

from scipy import stats

from cmath import rect, phase
from math import radians, degrees


#J# TODO: all these catalogs should be included on a input parameters of somethink like that

# In[5]:


# New Zealand

#cat = obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/NZfaults/SPUD_QUAKEML_bundle_2019-06-13T13.34.49.xml", "QUAKEML")  #New Zealand

#Japan

#cat = obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/JapanFaults/SPUD_QUAKEML_bundle_2019-08-28T08.46.22.xml", "QUAKEML")   # Japan

#Italy

#cat = obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/Italy/SPUD_QUAKEML_bundle_2019-09-24T11.09.18.xml", "QUAKEML")

#cat = np.genfromtxt("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/Italy/Italydataset1976-2015.csv",delimiter=',')

#SoutherCalifornia

#cat = obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/SouthernCalifornia/SPUD_QUAKEML_bundle_2019-10-31T16.14.52.xml","QUAKEML")

#Mediterranean South

#cat = obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/MediterraneanSouth_Area/SPUD_QUAKEML_bundle_2019-09-25T10.55.55.xml", "QUAKEML")

## Iceland

#cat=obspy.read_events(/home/jrodrig1/workspace/CHEESE/PD1/UCIS4EQ/code/components/dSPUD_QUAKEML_bundle_2019-10-31T11.28.02.xml","QUAKEML")
cat=obspy.read_events("/home/mmonterr/Documentos/CHEESE/PD1/CMT/Events_Comparison/HistoricalDataBase/Islandia/SPUD_QUAKEML_bundle_2019-10-31T11.28.02.xml", "QUAKEML")


NumEventsTotal = len(cat)

print(NumEventsTotal)


# In[7]:

#J# We need the following (for new event):
#J# - Magnitud (Mg)
#J# - (lat, long) position (Degrees)
#J# - Depth (Km)

#J# Create a JSON from the new event information + the algorithm setup

# Parameters
MagnitudThreshold = 5.0
k = 20  # kmax number maximo of neighbors
kmin = 0
distanciaMaxima = 30
random.seed(98) #98, 91, 1#10


###################### FOR QUAKEML DATABASES ##########################3
# Initialize vectors

dataLat = np.zeros((NumEventsTotal))
dataLon = np.zeros((NumEventsTotal))
dataMag = np.zeros((NumEventsTotal))
nodalPlan = np.zeros((NumEventsTotal,3))
dataCoordinates = np.zeros((NumEventsTotal,3))
dataDepth = np.zeros((NumEventsTotal))
focmecs = np.zeros((3))

i = 0

# For each event in the catalog, extract the FM, Mg and position
# (for events which mg >= MagnitudThreshold)
for e in cat:
    if  e.magnitudes[0]['mag'] >= MagnitudThreshold:
        b = e.focal_mechanisms[0]['nodal_planes'].nodal_plane_1  
        
        dataLat[i] = e.origins[0]['latitude']
        dataLon[i] = e.origins[0]['longitude']
        dataMag[i] = e.magnitudes[0]['mag']
        dataDepth[i] = e.origins[0]['depth']
        dataCoordinates[i,:] = [dataLon[i], dataLat[i],  dataDepth[i] ]         
        nodalPlan[i,0] = b.strike
        nodalPlan[i,1] = b.dip        
        nodalPlan[i,2] = b.rake 
        c = nodalPlan[i,:]
        focmecs = np.append(focmecs,c,axis=0)        
        i += 1    

# reshape the vector that has the focal mechanism information
NumTotal = i   

#J# Why the reshape is done? Figure out!
focmecs =  focmecs.reshape((NumTotal+1,3))

focmecs = np.delete(focmecs, (0), axis=0)
print(focmecs)

#J# Check the output for a better understanding and remove them!!!!
print(NumTotal)
print(min(dataMag))
print(min(dataMag[0:i]))
print(max(dataMag[0:i]))
print(max(dataDepth))
print(min(dataLat[0:i]))
print(max(dataLat[0:i]))
print(min(dataLon[0:i]))
print(max(dataLon[0:i]))

# Assuming the FM of an hypothetical new event


#Statistics over statistcal results
LoopStat = 1 #len(distanciaMaximaV)#15

#J# Remove this loop (only one iteration is needed).
for iloopStat in np.arange(LoopStat):
   
    numObser = NumTotal    # After filtering the whole catalog

    # Initialization
    nflag = 0 
    VectorDistances = np.zeros((NumTotal-1,8)) 
    mt2Prom = np.zeros([NumTotal,3]) 
    mt2Mediana = np.zeros([NumTotal,3]) 
    mt2Std = np.zeros([NumTotal,3]) 
    mt2StdPolar = np.zeros([NumTotal,3]) 
    mt2IQRPolar = np.zeros([NumTotal,3]) 
    mt2Clo = np.zeros([NumTotal,3]) 
    vecMagClo = np.zeros(NumTotal) 
    latiClo = np.zeros(NumTotal) 
    longClo = np.zeros(NumTotal)
    deptClo = np.zeros(NumTotal) 
    vecMagOri = np.zeros(NumTotal) 
    latiOri = np.zeros(NumTotal) 
    longOri = np.zeros(NumTotal) 
    deptOri = np.zeros(NumTotal)
    vecMagMediana = np.zeros([NumTotal,k]) 
    mt = np.zeros([NumTotal,3]) 
    mtOriginal = np.zeros([NumTotal,3]) 
    vecControl = np.zeros([NumTotal,2]) 
    mtFault= np.zeros([NumTotal,3]) 
    vecNumbNeig = np.zeros([NumTotal,1]) 
    vecMagOri = np.zeros([NumTotal,1]) 
    mt2MedianaStdPos = np.zeros([NumTotal,3]) 
    contEventosThresholdDist = -1

    mt2Clo2 = np.zeros([NumTotal,3])
    vecMagClo2 = np.zeros(NumTotal)
    latiClo2 = np.zeros(NumTotal)
    longClo2 = np.zeros(NumTotal)
    deptClo2 = np.zeros(NumTotal)
    mt2Clo3 = np.zeros([NumTotal,3])
    vecMagClo3 = np.zeros(NumTotal)
    latiClo3 = np.zeros(NumTotal)
    longClo3 = np.zeros(NumTotal)
    deptClo3 = np.zeros(NumTotal)
    mt2Clo4 = np.zeros([NumTotal,3])
    vecMagClo4 = np.zeros(NumTotal)
    latiClo4 = np.zeros(NumTotal)
    longClo4 = np.zeros(NumTotal)
    deptClo4 = np.zeros(NumTotal)
    print(NumTotal)

    #J# TODO: Remove this deprecated loop.
    for loopObservations in range(numObser):
        print("----------------------------------------------------------")
        print("###############Test-"+str(loopObservations)+"###########")
    # Each loop corresponds to a random set of Train-Test arrays
    
    #J# TODO: Modify this for using the whole catalog for NumTrain and take the 
    #J# input event as NumTest.
    
        NumTrain = NumTotal-1 # int(NumTotal*0.99)    
        NumTest = 1 #NumTotal-NumTrain   
        A = np.arange(0,NumTotal)
        sampling = random.sample(set(A),k=NumTrain)
        VecTrain = np.arange(NumTrain)
        VecTest = np.arange(NumTest)



        conTrain = 0
        conTest = 0
        #J# Remove this because our subset of events do match the whole set. 
        for i in np.arange(0,NumTotal):
            if i in sampling:        
                VecTrain[conTrain] = i
                conTrain += 1
            else:
                VecTest[conTest] = i
                conTest += 1    

        for NewEvent in range(0,NumTest):
            #J# this is input, so... remove it!
            NewEventLat =  dataLat[VecTest[NewEvent]]
            NewEventLon = dataLon[VecTest[NewEvent]] 
            NewEventDepth = dataDepth[VecTest[NewEvent]]
            NewEventMag = dataMag[VecTest[NewEvent]]
            
            #J# This the algorithm output (here is used as result's reference), 
            #J# so... remove it!
            #mtNumEvent = focmecs[VecTest[NewEvent]]
            
            # Initialization
            EuclideanDistances = np.zeros(NumTrain)
            coordEvent = np.zeros([NumTotal,2]);
            coordCloseEv = np.zeros([NumTotal,3]);
            coordFault = np.zeros([NumTotal,2]);

            # Calculate EuclideanDistances 
            for j in range(0,NumTrain):
                dataCoordinates = (dataLat[VecTrain[j]],dataLon[VecTrain[j]])
                dataCoordinatesNew = (NewEventLat, NewEventLon)
                data_sphereDist = haversine(dataCoordinates, dataCoordinatesNew) #Haversine distance in km
                data_DepthDist = (dataDepth[VecTrain[j]]/1000)- (NewEventDepth/1000)
                data_MagDist = dataMag[VecTrain[j]]-NewEventMag
                EuclideanDistances[j] = np.sqrt(data_sphereDist**2 + data_DepthDist**2)
                VectorDistances[j,:] = [j, EuclideanDistances[j], dataMag[VecTrain[j]], data_sphereDist, data_DepthDist, dataLat[VecTrain[j]],dataLon[VecTrain[j]] ,dataDepth[VecTrain[j]]/1000]

            # Sort by the EuclideanDistances         
            sortedArrUnifRes = VectorDistances[VectorDistances[:,1].argsort()]  
            #np.savetxt("sortedArrUnifRes.txt",sortedArrUnifRes)

            # Initialization
            mt2 =np.zeros([k,3])
            vecMagMed=np.zeros(k)
            latiMed=np.zeros(k)
            longMed=np.zeros(k)
            deptMed=np.zeros(k)

            invRakeEv = 0

            # Filter past-events given a Maximum distance threshold    
            contj = -1      
            for j in range(0,k):
                if sortedArrUnifRes[j, 1] < distanciaMaxima: #V[iloopStat]: 
                    vecMin = int(sortedArrUnifRes[j, 0])
                    contj += 1                
                    mt2[contj,:] = focmecs[VecTrain[vecMin]]  
                    vecMagMed[contj]=VectorDistances[vecMin,2]                
                    latiMed[contj]=VectorDistances[vecMin,5]
                    longMed[contj]=VectorDistances[vecMin,6]
                    deptMed[contj]=VectorDistances[vecMin,7]                

                mt2[contj,:] = focmecs[VecTrain[vecMin]]  



            def mean_angle(deg):
                return degrees(phase(sum(rect(1, radians(d)) for d in deg)/len(deg)))

            if contj <= kmin:
                #J# Write some mechanism for increasing the maximum distance 
                #J# threshold in order to obtain some data to compute. 
                #J# Notice Marisol!: Output the maximum distance used and
                #J# calculate the percentage of uncertainty
                #M# LA NUEVA DISTANCIA ENTRA EN LA RUTINA CMT-STATISTICS.py para saber el porcentaje de "éxito" en la determinacion del CMT
                print("no hay datos")                
                continue

            else:            
                # Initialize structures with data from above lines    
                contEventosThresholdDist += 1
                #print(contEventosThresholdDist)
                vecControl[contEventosThresholdDist,:] = [VecTest[NewEvent],NewEvent]
                mtOriginal[contEventosThresholdDist,:] = mt[NewEvent,:] 
                vecMagOri[contEventosThresholdDist] = dataMag[VecTest[NewEvent]]
                latiOri[contEventosThresholdDist] = NewEventLat
                longOri[contEventosThresholdDist] = NewEventLon
                deptOri[contEventosThresholdDist] = NewEventDepth           
                
                #J# That is the first line of each test in the printed output
                mt2Mediana[contEventosThresholdDist,0] = np.percentile(mt2[0:contj+1,0], 50, interpolation = 'midpoint')    
                mt2Mediana[contEventosThresholdDist,1] = np.percentile(mt2[0:contj+1,1], 50, interpolation = 'midpoint')    
                mt2Mediana[contEventosThresholdDist,2] = np.percentile(mt2[0:contj+1,2], 50, interpolation = 'midpoint')    
                    
                # How many neighbors has the current event
                vecNumbNeig[contEventosThresholdDist,0] = contj
               
                # Store K-nearest neighbors        
                mt2Clo[contEventosThresholdDist,:] = mt2[0,:]
                vecMagClo[contEventosThresholdDist] = vecMagMed[0]
                latiClo[contEventosThresholdDist] = latiMed[0]
                longClo[contEventosThresholdDist] = longMed[0]
                deptClo[contEventosThresholdDist] = deptMed[0]
                
                if contj > 4:
                    mt2Clo2[contEventosThresholdDist,:] = mt2[1,:]
                    vecMagClo2[contEventosThresholdDist] = vecMagMed[1]
                    latiClo2[contEventosThresholdDist] = latiMed[1]
                    longClo2[contEventosThresholdDist] = longMed[1]
                    deptClo2[contEventosThresholdDist] = deptMed[1]

                    mt2Clo3[contEventosThresholdDist,:] = mt2[2,:]
                    vecMagClo3[contEventosThresholdDist] = vecMagMed[2]
                    latiClo3[contEventosThresholdDist] = latiMed[2]
                    longClo3[contEventosThresholdDist] = longMed[2]
                    deptClo3[contEventosThresholdDist] = deptMed[2]

                    mt2Clo4[contEventosThresholdDist,:] = mt2[3,:]
                    vecMagClo4[contEventosThresholdDist] = vecMagMed[3]
                    latiClo4[contEventosThresholdDist] = latiMed[3]
                    longClo4[contEventosThresholdDist] = longMed[3]
                    deptClo4[contEventosThresholdDist] = deptMed[3]

                elif contj == 0:
                    mt2Clo2[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    mt2Clo3[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    mt2Clo4[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    vecMagClo2[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    vecMagClo3[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    vecMagClo4[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    latiClo2[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo2[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo2[contEventosThresholdDist] = deptClo[contEventosThresholdDist] 
                    latiClo3[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo3[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo3[contEventosThresholdDist] = deptClo[contEventosThresholdDist] 
                    latiClo4[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo4[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo4[contEventosThresholdDist] = deptClo[contEventosThresholdDist] 

                elif contj == 1:

                    mt2Clo2[contEventosThresholdDist,:] = mt2[1,:]
                    vecMagClo2[contEventosThresholdDist] = vecMagMed[1]
                    latiClo2[contEventosThresholdDist] = latiMed[1]
                    longClo2[contEventosThresholdDist] = longMed[1]
                    deptClo2[contEventosThresholdDist] = deptMed[1]

                    mt2Clo3[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    mt2Clo4[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    vecMagClo3[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    vecMagClo4[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    latiClo3[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo3[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo3[contEventosThresholdDist] = deptClo[contEventosThresholdDist] 
                    latiClo4[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo4[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo4[contEventosThresholdDist] = deptClo[contEventosThresholdDist] 

                elif contj == 2:

                    mt2Clo2[contEventosThresholdDist,:] = mt2[1,:]
                    vecMagClo2[contEventosThresholdDist] = vecMagMed[1]
                    latiClo2[contEventosThresholdDist] = latiMed[1]
                    longClo2[contEventosThresholdDist] = longMed[1]
                    deptClo2[contEventosThresholdDist] = deptMed[1]
                    mt2Clo3[contEventosThresholdDist,:] = mt2[2,:]
                    vecMagClo3[contEventosThresholdDist] = vecMagMed[2]
                    latiClo3[contEventosThresholdDist] = latiMed[2]
                    longClo3[contEventosThresholdDist] = longMed[2]
                    deptClo3[contEventosThresholdDist] = deptMed[2]
                    mt2Clo4[contEventosThresholdDist,:]  =  mt2Clo[contEventosThresholdDist,:] 
                    vecMagClo4[contEventosThresholdDist] = vecMagClo[contEventosThresholdDist]
                    latiClo4[contEventosThresholdDist] = latiClo[contEventosThresholdDist] 
                    longClo4[contEventosThresholdDist] = longClo[contEventosThresholdDist] 
                    deptClo4[contEventosThresholdDist] = deptClo[contEventosThresholdDist]               

                    
    
    ## Print possible options of FM ##
        
                print('## Median FM ##')
                print(mt2Mediana[contEventosThresholdDist,:])
    
                print('## closest k=1 ##')
                print(mt2Clo[contEventosThresholdDist,:])
            
                print('## closest k=2 ##')
                print(mt2Clo2[contEventosThresholdDist,:])
                
                print('## closest k=3 ##')
                print(mt2Clo3[contEventosThresholdDist,:])
                
                print('## closest k=4 ##')
                print(mt2Clo4[contEventosThresholdDist,:])
                
TotalPosPercen, NumDataUsed, PercenNumData = CMTStatistics(distanciaMaxima, dataLat, dataLon, dataDepth, dataMag, focmecs, NumTotal)
