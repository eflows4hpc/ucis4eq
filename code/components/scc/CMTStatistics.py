def CMTStatistics(distanciaMaxima, dataLat, dataLon, dataDepth, dataMag, focmecs, NumTotal)
#Statistics over statistcal results
distanciaMaximaV =  [distanciaMaxima]  #[20,30,40,50,60,70,80,90,100,110,120,130,140,150]
LoopStat = len(distanciaMaximaV)#15
#LoopStat = 15 #len(distanciaMaximaV)#15
LoopVectorPosi = np.zeros((LoopStat,6))
LoopVectorFalse = np.zeros((LoopStat,6))
LoopVectorNumbers = np.zeros(LoopStat)
#kminV = np.arange(15)

for iloopStat in np.arange(LoopStat):
    print("###############iloopStat###################",iloopStat)
    # Mediana con IQR/2 = qd
    numObser = NumTotal
    nflag = 0
    wSpatial = 1.0
    wMagnitu = 0.0
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
    vecMagMediana= np.zeros([NumTotal,k])
    latiMediana = np.zeros([NumTotal,k])
    longMediana = np.zeros([NumTotal,k])
    deptMediana = np.zeros([NumTotal,k])
    DeptMediana = np.zeros([NumTotal])
    vecFocalMecanismMed = np.zeros([NumTotal,k,3])
    mt2FaulClo = np.zeros([NumTotal,3])
    mt = np.zeros([NumTotal,3])
    mtOriginal = np.zeros([NumTotal,3])
    vecControl = np.zeros([NumTotal,2])    
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


    for loopObservations in range(numObser):
    # Each loop corresponds to a random set of Train-Test arrays
        NumTrain = NumTotal-1 # int(NumTotal*0.99)    
        NumTest = 1 #NumTotal-NumTrain   
        A = np.arange(0,NumTotal)
        sampling = random.sample(set(A),k=NumTrain)
        VecTrain = np.arange(NumTrain)
        VecTest = np.arange(NumTest)

        conTrain = 0
        conTest = 0
        for i in np.arange(0,NumTotal):
            if i in sampling:        
                VecTrain[conTrain] = i
                conTrain += 1
            else:
                VecTest[conTest] = i
                conTest += 1    

        for NewEvent in range(0,NumTest):
            NewEventLat =  dataLat[VecTest[NewEvent]]
            NewEventLon = dataLon[VecTest[NewEvent]] 
            NewEventDepth = dataDepth[VecTest[NewEvent]]
            NewEventMag = dataMag[VecTest[NewEvent]]
            mtNumEvent = focmecs[VecTest[NewEvent]]
            mtNumEvent1 =np.asarray(mtNumEvent)
            EuclideanDistances = np.zeros(NumTrain)
            coordEvent = np.zeros([NumTotal,2]);
            coordCloseEv = np.zeros([NumTotal,3]);
            coordFault = np.zeros([NumTotal,2]);

            for j in range(0,NumTrain):
                dataCoordinates = (dataLat[VecTrain[j]],dataLon[VecTrain[j]])
                dataCoordinatesNew = (NewEventLat, NewEventLon)
                data_sphereDist = haversine(dataCoordinates, dataCoordinatesNew) #Haversine distance in km
                data_DepthDist = (dataDepth[VecTrain[j]]/1000)- (NewEventDepth/1000)
                data_MagDist = dataMag[VecTrain[j]]-NewEventMag
                EuclideanDistances[j] = np.sqrt(wSpatial*(data_sphereDist**2 + data_DepthDist**2) + (wMagnitu* data_MagDist**2))
                VectorDistances[j,:] = [j, EuclideanDistances[j], dataMag[VecTrain[j]], data_sphereDist, data_DepthDist, dataLat[VecTrain[j]],dataLon[VecTrain[j]] ,dataDepth[VecTrain[j]]/1000]

            sortedArrUnifRes = VectorDistances[VectorDistances[:,1].argsort()]  
            #np.savetxt("sortedArrUnifRes.txt",sortedArrUnifRes)

            mt2 =np.zeros([k,3])
            vecMagMed=np.zeros(k)
            latiMed=np.zeros(k)
            longMed=np.zeros(k)
            deptMed=np.zeros(k)

            mt[NewEvent, :] = focmecs[VecTest[NewEvent]]

            invRakeEv = 0

            contj = -1      
            for j in range(0,k):
                if sortedArrUnifRes[j, 1] < distanciaMaximaV[iloopStat]: 
                    vecMin = int(sortedArrUnifRes[j, 0])
                    if (NewEventDepth/1000)-20 < VectorDistances[vecMin,7] < (NewEventDepth/1000)+20:
                        contj += 1                
                        mt2[contj,:] = focmecs[VecTrain[vecMin]]  
                        vecMagMed[contj]=VectorDistances[vecMin,2]                
                        latiMed[contj]=VectorDistances[vecMin,5]
                        longMed[contj]=VectorDistances[vecMin,6]
                        deptMed[contj]=VectorDistances[vecMin,7]                

                mt2[contj,:] = focmecs[VecTrain[vecMin]]  



            def mean_angle(deg):
                return degrees(phase(sum(rect(1, radians(d)) for d in deg)/len(deg)))

            if contj <= kmin: #V[iloopStat]:
                print("no hay datos")
                continue

            else:            

                contEventosThresholdDist += 1
                print(contEventosThresholdDist)
                vecControl[contEventosThresholdDist,:] = [VecTest[NewEvent],NewEvent]
                mtOriginal[contEventosThresholdDist,:] = mt[NewEvent,:] 
                vecMagOri[contEventosThresholdDist] = dataMag[VecTest[NewEvent]]
                latiOri[contEventosThresholdDist] = NewEventLat
                longOri[contEventosThresholdDist] = NewEventLon
                deptOri[contEventosThresholdDist] = NewEventDepth           

                mt2Mediana[contEventosThresholdDist,0] = np.percentile(mt2[0:contj+1,0], 50, interpolation = 'midpoint')    
                mt2Mediana[contEventosThresholdDist,1] = np.percentile(mt2[0:contj+1,1], 50, interpolation = 'midpoint')    
                mt2Mediana[contEventosThresholdDist,2] = np.percentile(mt2[0:contj+1,2], 50, interpolation = 'midpoint')    

                vecNumbNeig[contEventosThresholdDist,0] = contj

                for kk in range(0,contj+1):
                    vecMagMediana[contEventosThresholdDist,kk] = vecMagMed[kk]
                    latiMediana[contEventosThresholdDist,kk] = latiMed[kk]
                    longMediana[contEventosThresholdDist,kk] = longMed[kk]
                    deptMediana[contEventosThresholdDist,kk] = deptMed[kk]   
                    vecFocalMecanismMed[contEventosThresholdDist,kk,:] = mt2[kk,:]

                if  np.isnan(mt2StdPolar[contEventosThresholdDist,2]) == True:
                    print(np.isnan(mt2StdPolar[contEventosThresholdDist,2]), stddevDip, np.sqrt((contj+1)), (contj+1),"AQUI ERROR")

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

             
        
    
    plt.rcParams['figure.figsize'] = [20, 10]
    y_pos = range(0,contEventosThresholdDist+1)

    VectorMinMed = np.zeros(len(y_pos))
    VectorMinClo = np.zeros(len(y_pos))
    VectorMinClo2 = np.zeros(len(y_pos))
    VectorMinClo3 = np.zeros(len(y_pos))
    VectorMinClo4 = np.zeros(len(y_pos))
    VectorMinTotal = np.zeros(len(y_pos))
    MinTotalFault = np.zeros(len(y_pos))
    contMed = 0
    contClos1 = 0
    contClos2 = 0
    contClos3 = 0
    contClos4 = 0
    contMedF = 0
    contClos1F = 0
    contClos2F = 0
    contClos3F = 0
    contClos4F = 0
    
    for i in y_pos: 
        mtTest = mtOriginal[int(i),:]#focmecs[VecTest[int(i)]]
        t_test, p_test, b_test = eigenvectors(mtTest)
        t_medi, p_medi, b_medi = eigenvectors(mt2Mediana[int(i),:])
        t_clos, p_clos, b_clos = eigenvectors(mt2Clo[int(i),:])
        t_clos2, p_clos2, b_clos2 = eigenvectors(mt2Clo2[int(i),:])
        t_clos3, p_clos3, b_clos3 = eigenvectors(mt2Clo3[int(i),:])
        t_clos4, p_clos4, b_clos4 = eigenvectors(mt2Clo4[int(i),:])
  
        Min_Rot_Angle_Med = minRotAngles(t_test, p_test, b_test,t_medi, p_medi, b_medi,int(i))
        VectorMinMed[int(i)] = Min_Rot_Angle_Med   
        Min_Rot_Angle_Clo = minRotAngles(t_test, p_test, b_test,t_clos, p_clos, b_clos,int(i))
        VectorMinClo[int(i)] = Min_Rot_Angle_Clo    
        Min_Rot_Angle_Clo2 = minRotAngles(t_test, p_test, b_test,t_clos2, p_clos2, b_clos2,int(i))
        VectorMinClo2[int(i)] = Min_Rot_Angle_Clo2    
        Min_Rot_Angle_Clo3 = minRotAngles(t_test, p_test, b_test,t_clos3, p_clos3, b_clos3,int(i))
        VectorMinClo3[int(i)] = Min_Rot_Angle_Clo3    
        Min_Rot_Angle_Clo4 = minRotAngles(t_test, p_test, b_test,t_clos4, p_clos4, b_clos4,int(i))
        VectorMinClo4[int(i)] = Min_Rot_Angle_Clo4    
        minVectorMinAngle = min(VectorMinMed[i], VectorMinClo[i], VectorMinClo2[i], VectorMinClo3[i],VectorMinClo4[i])
        
        if minVectorMinAngle == VectorMinMed[i]:            
                if minVectorMinAngle <= 30:
                    contMed += 1
                else:
                    contMedF += 1
        elif minVectorMinAngle == VectorMinClo[i]: 
            if minVectorMinAngle <= 30:
                contClos1 += 1
            else:
                contClos1F += 1
        elif minVectorMinAngle == VectorMinClo3[i]:
            if VectorMinClo3[i] == VectorMinClo[i]:
                if minVectorMinAngle <= 30:
                    contClos1 += 1
                else:
                    contClos1F += 1
            else:
                if minVectorMinAngle <= 30:
                    contClos3 += 1
                else:
                    contClos3F += 1
        elif minVectorMinAngle == VectorMinClo2[i]:
            if VectorMinClo2[i] == VectorMinClo[i]:
                if minVectorMinAngle <= 30:
                    contClos1 += 1
                else:
                    contClos1F += 1
            else:
                if minVectorMinAngle <= 30:
                    contClos2 += 1
                else:
                    contClos2F += 1    
        elif minVectorMinAngle == VectorMinClo4[i]:
            if VectorMinClo4[i] == VectorMinClo[i]:
                if minVectorMinAngle <= 30:
                    contClos1 += 1
                else:
                    contClos1F += 1
            else:
                if minVectorMinAngle <= 30:
                    contClos4 += 1
                else:
                    contClos4F += 1  
        
        MinTotalFault[i] = minVectorMinAngle 
        

  #  VectorMinTotal[i] = minVectorMinAngle
    print("len(y_pos)",len(y_pos))
    print("contMed",contMed)
    print("contClos1",contClos1)
    print("contClos2",contClos2)
    print("contClos3",contClos3)
    print("contClos4",contClos4)
    
    TotalPosPercen = (contMed/len(y_pos)*100)+(contClos1/len(y_pos)*100)+(contClos2/len(y_pos)*100)+(contClos3/len(y_pos)*100)+(contClos4/len(y_pos)*100)
    print("TotalPosPercen",TotalPosPercen)
    LoopVectorPosi[iloopStat,:] = [contMed/len(y_pos)*100, contClos1/len(y_pos)*100,contClos2/len(y_pos)*100,contClos3/len(y_pos)*100,contClos4/len(y_pos)*100,TotalPosPercen]
    
    print("len(y_pos)",len(y_pos))
    print("contMedF",contMedF)
    print("contClos1F",contClos1F)
    print("contClos2F",contClos2F)
    print("contClos3F",contClos3F)
    print("contClos4F",contClos4F)
    
    TotalFalsPercen = (contMedF/len(y_pos))*100+(contClos1F/len(y_pos))*100+(contClos2F/len(y_pos))*100+(contClos3F/len(y_pos))*100+ (contClos4F/len(y_pos))*100
    print("TotalFalsPercen",TotalFalsPercen)
    LoopVectorFalse[iloopStat,:] = [contMedF/len(y_pos)*100, (contClos1F/len(y_pos))*100, (contClos2F/len(y_pos))*100, (contClos3F/len(y_pos))*100, contClos4F/len(y_pos)*100, TotalFalsPercen]    
    LoopVectorNumbers[iloopStat] = len(y_pos)
    
    return TotalPosPercen, len(y_pos), len(y_pos)/NumTotal
