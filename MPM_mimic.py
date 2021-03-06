import sys
sys.path.insert(0, "/home/gregor-pechstein/BOUT-dev/tools/pylib/") 
sys.path.insert(0, '../../tools/pylib/python_tools') 

from boutdata.collect import collect
from boututils.datafile import DataFile
import numpy as np
from boututils import calculus as calc
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from plot_MPM_mimic import Plot_I_sat
from plot_MPM_mimic import Plot_pin_distance
from plot_MPM_mimic import Plot_secondProbe
from plot_MPM_mimic import Plot_Inclination


def synthetic_probe(path='./blob_Hydrogen', WhatToDo='default', t_range=[100, 150], detailed_return=False, t_min=50, t_range_2P=[100,300],  t_range_start=np.arange(100,400,25) ,t_range_end=np.arange(150,450,25),inclin=np.arange(-0.003,0.0031,0.0005),distance=np.arange(0.001,0.011,0.001),distSecondProbe_x=0.005,distSecondProbe_z=np.arange(0.01,0.031,0.001),OneLine=False):
    
    """ Synthetic MPM probe for 2D blob simulations
    Follows same conventions as Killer, Shanahan et al., PPCF 2020.

    input: 

    path                       to BOUT++ dmp files 
    WhatToDo:                  which measurement should be done.  
                                    options:'Inclination','Pin_distance','I_sat','2Probes'
    t_range:                   time range for measurements (index)
    detailed_return (bool):    whether or not extra information is returned.
    t_min:                     minimun time to pass befor  start of measurement
    t_range_2P:                time range for measurements (index) with the 2. Probe
    t_range_start,t_range_end: beginn / end of different time ranges for I_sat. 
                                    Used if WhatToDo=='I_sat'
    inclin:                    inclination of probe head to magnetic surfaces.
                                    Used if WhatToDo=='Inclination'
    distance:                  distance between pins:center pin and upper/lower pin. 
                                    Used if WhatToDo=='Pin_distance'
    distSecondProbe_x:         distance between 1. and 2. Probe in x direction. 
                                    Used if WhatToDo=='2Probes'
    distSecondProbe_z:         distance between 1. and 2. Probe in z direction. 
                                    Used if WhatToDo=='2Probes'
    OneLine:                   only on horizontal Line is used for the measurement. 
                                    Used if WhatToDo=='default'

    returns:
    delta_measured -- measured blob size
    delta_real_mean -- real blob size
    vr_CA -- radial velocity (conditionally averaged)
    v -- COM velocity
    I_CA -- conditionally-averaged Saturation current density
    NrOfevents -- number of events measured

    optionally returns:
    t_e -- time-width of I_sat peak
    events -- locations of measurements
    blob_size_error -- error of the size estimation
    velocity_error_1Probe -- velocity error at the first Probe
    twindow

    additional returns if: WhatToDo=='Inclination'
        inclinationAngle
    additional returns if: WhatToDo=='2Probes'
        velocity_error_2Probe -- velocity error at the first Probe
        velocity_error_direct -- velocity error direkt measurment ( event at 1. and 2. Probe)
        vr_2P -- radial velocity calculated from radial offset and delta t between ( event at 1. and 2. Probe)
        vr_CA_2P -- radial velocity (conditionally averaged) at the 2. Probe
        events_2Probes -- number of events measured at the 2. Probe
 
    """
     
    
    n, Pe,n0,T0,Lx,Lz,B0,phi,dt, t_array =loading_data (path)
    tsample_size = t_range[-1] - t_range[0]
    trange = np.linspace(t_range[0], t_range[-1] - 1, tsample_size, dtype='int')
    nt=n.shape[0]
    t_A=[t_range[0],nt-t_range[1]]
    I, J0, Imax, Imin = finding_Isat(n, Pe, n0,T0)

    delta_real_mean, Rsize_mean, Zsize_mean, blob_deformation= real_size(n, trange, tsample_size, Lx, Lz)

    v, pos_fit, pos, r, z, t = calc_com_velocity(path=path, fname=None)

    ###Selecting What to do ###

    if (WhatToDo=='Inclination'):
        ### default pin distance of 5 mm ###
        pin_distance=np.array((0.005, 0.005))
        delta_measured, vr_CA, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow,inclinationAngle =inclinationOfProbe(path,t_range,trange,dt,t_min,t_A,inclin, pin_distance,I, phi, B0, Lx, Lz, Imin, Imax,v,z,delta_real_mean,J0,OneLine)
        if not detailed_return:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents
        else:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow,inclinationAngle

    elif(WhatToDo=='Pin_distance'):
        ### default inclination = 0 ###
        inclination=0
        delta_measured,velocity_error_1Probe, blob_size_error, NrOfevents, vr_CA, I_CA, t_e, twindow, events =pin_distance_variation(path,distance, I, phi, B0, Lx, Lz, Imin, Imax,inclination,t_min,trange,t_range,dt, t_A,v,z,delta_real_mean,J0,OneLine)
        if not detailed_return:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents
        else:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow
        
    elif(WhatToDo=='I_sat'):
        ### default pin distance of 5 mm  ###
        ### default inclination = 0 ###
        pin_distance=np.array((0.005, 0.005))
        inclination=0
        t_range=np.array((t_range_start,t_range_end))
        t_range=np.transpose(t_range)
        I_CA, vr_CA, t_range,t_array, blob_size_error,velocity_error_1Probe, twindow, NrOfevents, t_e,  v_pol,delta_measured,delta_real_mean,events=I_sat(path, t_range,nt,n,Lx,Lz,I, phi, B0,Imin, Imax,pin_distance,inclination,t_min,dt,v,z, t_array,J0,OneLine)
        if not detailed_return:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents
        else:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow
    elif(WhatToDo=='2Probes'):
        ### default pin distance of 5 mm  ###
        ### default inclination = 0 ###
        
        pin_distance=np.array((0.005, 0.005))
        inclination=0
        t_A_2P=[t_range_2P[0],nt-t_range_2P[1]]
        velocity_error_1Probe, velocity_error_2Probe, velocity_error_direct, twindow, vr_CA, vr_2P, vr_CA_2P, events_2Probes,t_range, t_range_2P,t_index2P, I_CA, NrOfevents,t_e, events, blob_size_error, delta_measured= Varying_dsToSecondProbe(path,I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min,trange,t_range,t_array,t_range_2P,dt, t_A,distSecondProbe_x,distSecondProbe_z,v,t_A_2P,J0,delta_real_mean,z,OneLine)
        if not detailed_return:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents
        else:
            return delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow,velocity_error_2Probe, velocity_error_direct, vr_2P, vr_CA_2P, events_2Probes

    else:
        # default 
        # t_A=[50,150]
        pin_distance=np.array((0.005, 0.005))
        inclination=0
        trise, Epol,vr, events, inclinationAngle,d_Potential_mean =geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min)
        # only one horizontal line is used for the simulated measurment 
        if (OneLine==True):
            nz = I.shape[2]
            z_pos=int((np.mean(z[t_range]) / Lz) * nz)
            trise=trise[:,z_pos]
            Epol=Epol[:,:,z_pos]
            vr=vr[:,:,z_pos]
            I=I[:,:,z_pos]
            events=events[:,z_pos]
            
        t_e, vr_CA, I_CA, twindow,event_indices = average_messurments(trise,Epol,vr,events,I,Imin, Imax,trange,dt, t_A,OneLine)
        I_CA= I_CA-J0

        v_pol = (np.max(z[t_range[0]:t_range[1]-1]) - z[t_range[0]]) / (dt * len(trange))
        delta_measured = t_e * v_pol   
        v_in_t_range=v[t_range[0]:t_range[1]-1]
        velocity_error_1Probe =np.abs(100* (np.max(v_in_t_range) - np.max(vr_CA)) / np.max(v_in_t_range))
        blob_size_error =np.abs( 100*( delta_real_mean-delta_measured) / delta_real_mean)
        NrOfevents=len(event_indices)
        mean_phi_dist=np.mean(d_Potential_mean[t_range[0]:t_range[1]-1])
        print ("Number of events: {} ".format(np.around(NrOfevents, decimals=2)))
        print ("Real Blob size in mm: {} ".format(np.around(delta_real_mean*1e3, decimals=2)))
        print ("Size measurement error: {}% ".format(np.around(blob_size_error, decimals=2)))
        print ("Velocity measurement error: {}% ".format(np.around(velocity_error_1Probe, decimals=2)))
        print ("Distance between Max/min of the Potential in mm: {} ".format(np.around(mean_phi_dist*1e3, decimals=2)))
        
        if not detailed_return:
            return  delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents
        else:
            return  delta_measured, delta_real_mean, vr_CA, v, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow



def I_sat(path, t_range,nt,n,Lx,Lz,I, phi, B0,Imin, Imax,pin_distance,inclination,t_min,dt,v,z,t_array,J0,OneLine):

    """
    calculating I_sat for different time range for the  measurement

    """

    
    trise, Epol,vr, events, inclinationAngle,d_Potential_mean =geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min)

    t_A=np.transpose(np.array((t_range[:,0],nt-t_range[:,1])))
    tsample_size = t_range[:,-1] - t_range[:,0]

    delta_real_mean=np.zeros(t_range.shape[0])
    Rsize_mean=np.zeros(t_range.shape[0])
    Zsize_mean=np.zeros(t_range.shape[0])
    blob_deformation=np.zeros(t_range.shape[0])
    trange=np.zeros((tsample_size[0],t_range.shape[0]),dtype='int')
    NrOfevents=np.zeros(t_range.shape[0])
    t_e=np.zeros(t_range.shape[0])
    v_pol=np.zeros(t_range.shape[0])
    vr_CA=np.zeros((t_A[0,0]+t_A[0,1],t_range.shape[0]))
    I_CA=np.zeros((t_A[0,0]+t_A[0,1],t_range.shape[0]))
    twindow=np.zeros((t_A[0,0]+t_A[0,1],t_range.shape[0]))
    v_in_t_range=np.zeros((tsample_size[0],t_range.shape[0]))
    
    #stepping through the different time windows of observation 
    for ii in range(t_range.shape[0]):
        trange[:,ii] = np.linspace(t_range[ii,0], t_range[ii,-1] - 1, tsample_size[ii], dtype='int')
        delta_real_mean[ii], Rsize_mean[ii], Zsize_mean[ii], blob_deformation[ii]= real_size(n, trange[:,ii], tsample_size[ii], Lx, Lz)        

        t_e[ii], vr_CA[:,ii], I_CA[:,ii], twindow[:,ii],event_indices = average_messurments(trise,Epol,vr,events,I,Imin, Imax,trange[:,ii],dt, t_A[ii,:],OneLine)
 

        NrOfevents[ii]=len(event_indices)
        v_pol[ii] = (np.max(z[t_range[ii,0]:t_range[ii,1]-1]) - z[t_range[ii,0]]) / (dt * len(trange[:,ii]))
        v_in_t_range[:,ii]=v[t_range[ii,0]:t_range[ii,1]]
    
    
    I_CA= I_CA-J0
    delta_measured =np.multiply(t_e , v_pol)  
    
    #calcualtion the velocity error and the size error
    velocity_error_1Probe =np.abs(100* (np.max(v_in_t_range,axis=0) - np.max(vr_CA,axis=0)) / np.max(v_in_t_range,axis=0))
    blob_size_error =np.abs( 100*( delta_real_mean-delta_measured) / delta_real_mean)
        
    print ("Number of events: {} ".format(np.around(NrOfevents, decimals=2)))
    print ("Size measurement error: {}% ".format(np.around(blob_size_error, decimals=2)))
    print ("Real Blob size in mm: {} ".format(np.around(delta_real_mean*1e3, decimals=2)))
    print ("Velocity measurement error: {}% ".format(np.around(velocity_error_1Probe, decimals=2)))

    np.savez(path+"/I_sat",I_CA=I_CA, vr_CA=vr_CA, t_range=t_range, t_array=t_array, blob_size_error=blob_size_error, velocity_error_1Probe=velocity_error_1Probe, twindow=twindow, NrOfevents=NrOfevents, t_e=t_e,  v_pol= v_pol, delta_measured=delta_measured, delta_real_mean=delta_real_mean)
    

    Plot_I_sat(path,delta_measured,blob_size_error,twindow,I_CA,t_array,t_range)

    return I_CA, vr_CA, t_range,t_array, blob_size_error,velocity_error_1Probe, twindow, NrOfevents, t_e,  v_pol,delta_measured,delta_real_mean,events


        

def pin_distance_variation(path,distance,I, phi, B0, Lx, Lz, Imin, Imax,inclination,t_min,trange,t_range,dt, t_A,v,z,delta_real_mean,J0,OneLine):
    
    """
    calculates vr_CA and the velocity error for different pin distances and plots a graphs

    """

    vr_CA=np.zeros((t_A[1]+t_A[0],distance.shape[0]))
    # geting the measured vr_CA for diffrent pin seperations
    for ii in range(distance.shape[0]):
        pin_distance=[distance[ii],distance[ii]]
        trise, Epol,vr, events, inclinationAngle,d_Potential_mean =geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min)

        t_e, vr_CA[:,ii], I_CA, twindow,event_indices = average_messurments(trise,Epol,vr,events,I,Imin, Imax,trange,dt, t_A,OneLine)
    
    I_CA= I_CA-J0 
    v_pol = (np.max(z[t_range[0]:t_range[1]-1]) - z[t_range[0]]) / (dt * len(trange))
    delta_measured = t_e * v_pol     
    v_in_t_range=v[t_range[0]:t_range[1]-1]
 
    # velocity error is calculated 
    velocity_error_1Probe =np.abs(100* (np.max(v_in_t_range) - np.max(vr_CA,axis=0)) / np.max(v_in_t_range))
    blob_size_error =np.abs( 100*( delta_real_mean-delta_measured) / delta_real_mean)
    NrOfevents=len(event_indices)
    mean_phi_dist=np.mean(d_Potential_mean[t_range[0]:t_range[1]-1])
    print ("Number of events: {} ".format(np.around(NrOfevents, decimals=2)))
    print ("Real Blob size in mm: {} ".format(np.around(delta_real_mean*1e3, decimals=2)))
    print ("Size measurement error: {}% ".format(np.around(blob_size_error, decimals=2)))
    print ("Velocity measurement error: {}% ".format(np.around(velocity_error_1Probe, decimals=2)))
    print ("Distance between Max/min of the Potential in mm: {} ".format(np.around(mean_phi_dist*1e3, decimals=2)))
    twindow*=1e6

    np.savez(path+"/pin_distance",velocity_error_1Probe=velocity_error_1Probe,blob_size_error =blob_size_error,NrOfevents=NrOfevents,vr_CA=vr_CA,distance=distance,twindow=twindow, delta_measured=delta_measured, delta_real_mean=delta_real_mean)


    Plot_pin_distance(path,distance,velocity_error_1Probe,twindow,vr_CA,v_in_t_range)
    
    return  delta_measured,velocity_error_1Probe,blob_size_error,NrOfevents,vr_CA, I_CA, t_e, twindow, events

        

def Varying_dsToSecondProbe(path,I, phi, B0, Lx, Lz, Imin, Imax, pin_distance, inclination, t_min,trange, t_range ,t_array,t_range_2P,dt, t_A,distSecondProbe_x,distSecondProbe_z,v,t_A_2P,J0,delta_real_mean,z,OneLine):

    """
    finding the velocity error for different vertical offsets and fixed horizontal offset


    """
    
    # measuring with the first probe
    trise, Epol,vr, events, inclinationAngle,d_Potential_mean =geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min)

    t_e, vr_CA, I_CA, twindow,event_indices = average_messurments(trise,Epol,vr,events,I,Imin, Imax,trange,dt, t_A,OneLine)
    I_CA= I_CA-J0

    vr_2P=np.zeros(distSecondProbe_z.shape[0])
    v_pol_2P=np.zeros(distSecondProbe_z.shape[0])
    NrOfevents_2P=np.zeros(distSecondProbe_z.shape[0])
    events_2Probes=np.zeros(distSecondProbe_z.shape[0])

    nx = trise.shape[0]
    nz = trise.shape[1]
    dist_probeheads_x= int((distSecondProbe_x / Lx) * nx)

    vr_CA_2P=np.zeros((t_A_2P[1]+t_A_2P[0],distSecondProbe_z.shape[0]))
    t_e_2P=np.zeros(distSecondProbe_z.shape[0])
    I_CA_2P=np.zeros((t_A_2P[1]+t_A_2P[0],distSecondProbe_z.shape[0]))
    t_e_2P=np.zeros(distSecondProbe_z.shape[0])

    # determin measurments at the 2. Probe 
    for dd in range(distSecondProbe_z.shape[0]):
        dist_probeheads_z= int((distSecondProbe_z[dd] / Lz) * nz)
        trise_2P_pre=trise[dist_probeheads_x:,:]

        vr_2P[dd],v_pol_2P[dd], delta_t_measured, t_index2P, delta_t, events_2Probes[dd] = second_prob( t_array, Lx,Lz, trise, t_range, t_range_2P, dist_probeheads_z,dist_probeheads_x,distSecondProbe_x,distSecondProbe_z[dd])
        
        trise_2P=np.multiply(trise_2P_pre,t_index2P) 

        t_e_2P[dd], vr_CA_2P[:,dd], I_CA_2P[:,dd], twindow_2P,event_indices_2P = average_messurments(trise_2P,Epol[:,dist_probeheads_x:,:],vr[:,dist_probeheads_x:,:],events[dist_probeheads_x:,:],I[:,dist_probeheads_x:,:],Imin, Imax,t_range_2P,dt, t_A_2P,OneLine)
        NrOfevents_2P[dd]=len(event_indices_2P)

    I_CA_2P= I_CA_2P-J0
    v_pol = (np.max(z[t_range[0]:t_range[1]-1]) - z[t_range[0]]) / (dt * len(trange))
    delta_measured_1P = t_e * v_pol

    v_in_t_range=v[t_range[0]:t_range[1]-1] 
    v_pol_error =np.abs(100* (v_pol - v_pol_2P) / v_pol)

    # velocity error is calculated 
    velocity_error_1Probe =np.abs(100* (np.max(v_in_t_range) - np.max(vr_CA)) / np.max(v_in_t_range))
    velocity_error_direct =np.abs(100* (np.max(v_in_t_range) - vr_2P) / np.max(v_in_t_range))
    velocity_error_2Probe =np.abs(100* (np.max(v_in_t_range) - np.max(vr_CA_2P,axis=0)) / np.max(v_in_t_range))
    blob_size_error_1P =np.abs( 100*( delta_real_mean-delta_measured_1P) / delta_real_mean)

    NrOfevents=len(event_indices)
    mean_phi_dist=np.mean(d_Potential_mean[t_range[0]:t_range[1]-1])

    np.savez(path+"/2Probe",velocity_error_1Probe=velocity_error_1Probe, velocity_error_2Probe=velocity_error_2Probe, velocity_error_direct=velocity_error_direct, twindow=twindow, vr_CA=vr_CA, vr_2P=vr_2P, vr_CA_2P=vr_CA_2P, events_2Probes=events_2Probes,t_range=t_range, t_range_2P= t_range_2P,t_index2P=t_index2P,distSecondProbe_x=distSecondProbe_x, distSecondProbe_z=distSecondProbe_z)
 
    print("Number of events 1. Probe: {} ".format(np.around(NrOfevents, decimals=2)))
    print("Number of events 2. Probe: {} ".format(np.around(NrOfevents_2P, decimals=2)))
    print ("Real Blob size in mm: {} ".format(np.around(delta_real_mean*1e3, decimals=2)))
    print ("Size measurement error: {}% ".format(np.around(blob_size_error_1P, decimals=2)))
    print("Velocity measurement error 1 Probe: {}% ".format(np.around(velocity_error_1Probe, decimals=2)))
    print("Velocity measurement error 2 Probe: {}% ".format(np.around(velocity_error_2Probe, decimals=2)))
    print("Velocity measurement error direkt Probe: {}% ".format(np.around(velocity_error_direct, decimals=2)))
    print ("Distance between Max/min of the Potential in mm: {} ".format(np.around(mean_phi_dist*1e3, decimals=2)))

    Plot_secondProbe(path, distSecondProbe_z, velocity_error_1Probe, velocity_error_2Probe, velocity_error_direct, v_pol_error)

    return velocity_error_1Probe, velocity_error_2Probe, velocity_error_direct, twindow, vr_CA, vr_2P, vr_CA_2P, events_2Probes,t_range, t_range_2P,t_index2P, I_CA, NrOfevents,t_e, events, blob_size_error_1P, delta_measured_1P



def inclinationOfProbe(path,t_range,trange,dt,t_min,t_A,inclin, pin_distance,I, phi, B0, Lx, Lz, Imin, Imax,v,z,delta_real_mean,J0,OneLine):

    """
    findes the velocity error for different inclinations of the outer probes
   

    """
    
    vr_CA=np.zeros((t_A[1]+t_A[0],inclin.shape[0]))
    inclinationAngle=np.zeros(inclin.shape[0])

    # geting the measured vr_CA for diffrent inclinations
    for ii in range(inclin.shape[0]):
        trise, Epol,vr, events,inclinationAngle[ii],d_Potential_mean =geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclin[ii],t_min)

        t_e, vr_CA[:,ii], I_CA, twindow,event_indices = average_messurments(trise,Epol,vr,events,I,Imin, Imax,trange,dt,t_A,OneLine)

    I_CA= I_CA-J0
    v_pol = (np.max(z[t_range[0]:t_range[1]-1]) - z[t_range[0]]) / (dt * len(trange))
    delta_measured = t_e * v_pol

    # velocity error is calculated 
    v_in_t_range=v[t_range[0]:t_range[1]-1] 
    velocity_error_1Probe = np.abs(100* (np.max(v_in_t_range) - np.max(vr_CA, axis=0)) / np.max(v_in_t_range))
    blob_size_error =np.abs( 100*( delta_real_mean-delta_measured) / delta_real_mean)
    NrOfevents=len(event_indices)

    print("Number of events: {} ".format(np.around(NrOfevents, decimals=2)))
    print ("Real Blob size in mm: {} ".format(np.around(delta_real_mean*1e3, decimals=2)))
    print("Size measurement error: {}% ".format(np.around(blob_size_error, decimals=2)))
    print("Velocity measurement error 1 Probe: {}% ".format(np.around(velocity_error_1Probe, decimals=2)))

    twindow*=1e6
    np.savez(path+"/inclination2",velocity_error_1Probe=velocity_error_1Probe,twindow=twindow, vr_CA=vr_CA,I_CA=I_CA, inclin=inclin,inclinationAngle=inclinationAngle, v=v, t_range=t_range,t_e=t_e, NrOfevents=NrOfevents, delta_measured=delta_measured, delta_real_mean=delta_real_mean)

    Plot_Inclination(path,inclinationAngle, twindow,vr_CA,v_in_t_range, I_CA,velocity_error_1Probe)


    return delta_measured, vr_CA, I_CA, NrOfevents,t_e, events, blob_size_error, velocity_error_1Probe, twindow,inclinationAngle


def loading_data(path):

    """
    collecting the data from the BOUT++ simulations 
    normalizing to SI units (not all)
    input:
    path: to BOUT++ dmp files

    return:
    n, Pe,n0,T0,Lx,Lz,B0,phi,dt, t_array
    """
    
    n = collect("Ne", path=path, info=False)
    Pe = collect("Pe", path=path, info=False)
    n0 = collect("Nnorm", path=path, info=False)
    T0 = collect("Tnorm", path=path, info=False)
    phi = collect("phi", path=path, info=False) * T0
    phi -= phi[0, 0, 0, 0]
    wci = collect("Omega_ci", path=path, info=False)
    t_array = collect("t_array", path=path, info=False)/wci
    dt = (t_array[1] - t_array[0]) 
    rhos = collect('rho_s0', path=path, info=False)
    R0 = collect('R0', path=path, info=False) * rhos
    B0 = collect('Bnorm', path=path, info=False)
    dx = collect('dx', path=path, info=False) * rhos * rhos
    dz = collect('dz', path=path, info=False)
    Lx = ((dx.shape[0] - 4) * dx[0, 0]) / (R0)
    Lz = dz * R0 * n.shape[-1]


    n = n[:, :, 0, :]
    Pe = Pe[:, :, 0, :]
    return n, Pe,n0,T0,Lx,Lz,B0,phi,dt, t_array

def second_prob(t_array,Lx,Lz,trise, t_range, t_range_2P, dist_probeheads_z,dist_probeheads_x,distSecondProbe_x, distSecondProbe_z):
    """
    a second Probe is used to determine the radial velocity
    finding events at the 2. Probe under the condition that at the 1. probe the threshold has been surpassed
   
    input:
    t_array:
    Lx,Lz:
    trise:             time of event at position x,z
    t_range:           time range for measurements (index)
    t_range_2P:        time range for measurements (index) with the 2. Probe
    dist_probeheads_z: index vertical offset 2. Probe 
    dist_probeheads_x: index horizontal offset 2. Probe
    distSecondProbe_x: vertical offset 2. Probe in m
    distSecondProbe_z: horizontal offset 2. Probe in m

    return:
    vr_2Probs:        radial velocity calculated from delta t and horizontal offset
    v_pol_2Probs:     poloidal velocity calculated from delta t and vertical offset
    delta_t_measured: time between event at 1. and 2. Probe
    twindow:           
    delta_t:          
    events_2Probes:   Number of events at the 2. Probe

    """
    
    nx = trise.shape[0]
    nz = trise.shape[1]
    delta_t=np.zeros((nx-dist_probeheads_x, nz))
    events_SecProbe=np.zeros((nx-dist_probeheads_x, nz), dtype=int)

    for k in np.arange(0, nz):
        for i in np.arange(0, nx-dist_probeheads_x):
            if (t_array[int(trise[i,k])]>0) and (t_array[int(trise[i+dist_probeheads_x,(k+dist_probeheads_z) % (nz - 1)])]>0):
                events_SecProbe[i, k] = 1
                delta_t[i,k]=t_array[int(trise[i+dist_probeheads_x,(k+dist_probeheads_z) % (nz - 1)])]-t_array[int(trise[i,k])]


    twindow1=np.zeros((nx-dist_probeheads_x, nz))
    twindow2=np.zeros((nx-dist_probeheads_x, nz))
    for k in np.arange(0, nz):
        for i in np.arange(0, nx-dist_probeheads_x):
            for t in np.arange(t_range[0], t_range[-1]):
                if (trise[i,k]>=t_range[0]) and (trise[i,k]<t_range[-1]):
                    twindow1[i,k]=1
                if (trise[i+dist_probeheads_x,(k+dist_probeheads_z) % (nz - 1)]>=t_range_2P[0]) and (trise[i+dist_probeheads_x,(k+dist_probeheads_z) % (nz - 1)]<t_range_2P[-1]):
                    twindow2[i,k]=1
    twindow=np.multiply(twindow1,twindow2)

    delta_t_measured=np.mean(delta_t[twindow==1])   
    events_2Probes=len(delta_t[twindow==1])
    vr_2Probs=distSecondProbe_x/delta_t_measured
    v_pol_2Probs=distSecondProbe_z/delta_t_measured

    return vr_2Probs, v_pol_2Probs, delta_t_measured, twindow, delta_t, events_2Probes


def finding_Isat(n, Pe, n0, T0):
    """
    calcualtion the ion saturation current
    input:
    n:  Plasma density (normalized)
    Pe: Electron pressure
    n0: nominal density
    T0 : Temperatur

    return 
    I: Ion saturation current density
    J0: I_sat outside a blob
    Imax/Imin: maximum /minimum I_sat at t=0 
    """
    qe = 1.602176634e-19
    m_i = 1.672621898e-27

    P = Pe * T0 * n0
    Te = np.divide(P, n * n0)

    J_factor = n0 * 0.49 * qe * np.sqrt((qe * Te) / (m_i)) * 1e-3

    J0 = n0 * 0.49 * qe * np.sqrt((qe * T0) / (m_i)) * 1e-3
    I = np.multiply(n, J_factor)

    Imax, Imin = np.amax((I[0, :, :])), np.amin((I[0, :, :]))

    return I, J0, Imax, Imin


def geting_messurments(I, phi, B0, Lx, Lz, Imin, Imax,pin_distance,inclination,t_min ):

    """
    finding the grid point at witch I_sat surpasses the threshold for the first time
    
    input:
    I:            Ion saturation current density
    phi           Potential
    B0            Magnetic field
    Lx/ Lz
    Imin/ Imax:   maximum /minimum I_sat at t=0 
    pin_distance: distance between pins:center pin and upper/lower pin
    inclination:  inclination of probe head to magnetic surfaces
    t_min         minimun time to pass befor  start of measurement

    return:
    trise:               time of event at position x,z
    Epol:                Poloidal Electric field between outer pins
    vr:                  radial velocity of the blob 
    events:              events
    inclinationAngle:    Angle between outside Probe and poloidal direction
    d_Potential_mean:    distance between max / min of Potential
    """
    
    nt = I.shape[0]
    nx = I.shape[1]
    nz = I.shape[2]
    

    probe_offset = [int((pin_distance[0] / Lz) * nz), int((pin_distance[1] / Lz) * nz)]
    probe_misalignment = int((inclination / Lx) * nx)
    # distance between outer probs
    d = np.sqrt((np.sum(pin_distance)) ** 2 + (2 * inclination) ** 2)
    inclinationAngle=np.arcsin(inclination/d)
    Epol = np.zeros((nt, nx, nz))
    vr = np.zeros((nt, nx, nz))
    events = np.zeros((nx, nz))
    trise = np.zeros((nx, nz))
    for k in np.arange(0, nz):
        for i in np.arange(0, nx):
            if (np.any(I[t_min:, i, k] > Imin + 0.368 * (Imax - Imin))):
                trise[i, k] = int(np.argmax(I[t_min:, i, k] > Imin + 0.368 * (Imax - Imin)) + t_min)
                events[i, k] = 1
                Epol[:, i, k] = (phi[:, (i + probe_misalignment), 0, (k + probe_offset[0]) % (nz - 1)] - phi[:, (i - probe_misalignment), 0, (k - probe_offset[1]) % (nz - 1)]) / d
                vr[:, i, k] = Epol[:, i, k] / B0

    phi=phi[:,:,0,:]

    phi_distance=np.zeros(nt)
    for tt in np.arange(0,nt):
        index_max= np.where(phi[tt,:,:]==np.max(phi[tt,:,:]))
        index_min= np.where(phi[tt,:,:]==np.min(phi[tt,:,:]))
        index_max_z=index_max[1]
        index_max_z=index_max_z[0]
        index_min_z=index_min[1]
        index_min_z=index_min_z[0]
        phi_distance[tt]=index_max_z-index_min_z
    d_Potential_mean=(phi_distance/nz)*Lz

    return trise, Epol,vr, events,inclinationAngle,d_Potential_mean


def average_messurments(trise,Epol,vr,events,I, Imin, Imax,trange,dt,t_A,OneLine):

    """
    the measured velocity and I_sat are selected in the time range of the measurements 

    input:
    trise:               time of event at position x,z
    Epol:                Poloidal Electric field between outer pins
    vr:                  radial velocity of the blob 
    events:              events
    I                    Ion saturation current density
    Imin/Imax            maximum /minimum I_sat at t=0 
    trange
    dt
    t_A
    OneLine

    return:
    t_e
    vr_CA,
    I_CA
    twindow
    event_indices

    """
    
    nt = I.shape[0]
    nx = I.shape[1]
    if (OneLine==True):
        nz=1
    else:
        nz = I.shape[2]
    
    trise_flat = trise.flatten()
    events_flat = events.flatten()
    Epol_flat = Epol.reshape(nt, nx * nz)
    vr_flat = vr.reshape(nt, nx * nz)
    I_flat = I.reshape(nt, nx * nz)


    vr_offset = np.zeros((t_A[1]+t_A[0], nx * nz))
    I_offset = np.zeros((t_A[1]+t_A[0], nx * nz))
    event_indices = []
    for count in np.arange(0, nx * nz):
        for t in np.arange(trange[0], trange[-1]):
            if (t == np.int(trise_flat[count])):
                event_indices.append(count)
                vr_offset[:, count] = vr_flat[np.int(trise_flat[count]) - t_A[0]:np.int(trise_flat[count] + t_A[1]), count]
                I_offset[:, count] = I_flat[np.int(trise_flat[count]) - t_A[0]:np.int(trise_flat[count] + t_A[1]), count]


    vr_CA = np.mean(vr_offset[:, event_indices], axis=-1)
    I_CA = np.mean(I_offset[:, event_indices], axis=-1)
    twindow = np.linspace(-t_A[0] * dt, t_A[1] * dt, t_A[1]+t_A[0])
    tmin, tmax = np.min(twindow[I_CA > Imin + 0.368 * (Imax - Imin)]), np.max(
        twindow[I_CA > Imin + 0.368 * (Imax - Imin)])
    t_e = tmax - tmin



    return t_e, vr_CA, I_CA, twindow,event_indices


def real_size(n, trange, tsample_size, Lx, Lz):
    
    """
    geting the real blob size calculated
    input:
    n: plasma density
    tsample_size: number of time points in the measured time window 
    Lx,Lz:

    return:
    delta_real_mean, Rsize_mean, Zsize_mean,blob_deformation
    """
    
    n_real = n[trange, :, :]
    n_real_max = np.zeros((tsample_size))
    n_real_min = np.zeros((tsample_size))
    Rsize = np.zeros((tsample_size))
    Zsize = np.zeros((tsample_size))
    delta_real = np.zeros((tsample_size))
    for tind in np.arange(0, tsample_size):
        n_real_max[tind], n_real_min[tind] = np.amax((n[trange[tind], :, :])), np.amin((n[trange[tind], :, :]))
        n_real[tind, n_real[tind] < (n_real_min[tind] + 0.368 * (n_real_max[tind] - n_real_min[tind]))] = 0.0
        R = np.linspace(0, Lx, n.shape[1])
        Z = np.linspace(0, Lz, n.shape[-1])
        RR, ZZ = np.meshgrid(R, Z, indexing='ij')
        Rsize[tind] = np.max(RR[np.nonzero(n_real[tind])]) - np.min(RR[np.nonzero(n_real[tind])])
        Zsize[tind] = np.max(ZZ[np.nonzero(n_real[tind])]) - np.min(ZZ[np.nonzero(n_real[tind])])
        delta_real[tind] = np.mean([Rsize[tind], Zsize[tind]])

    delta_real_mean = np.mean(delta_real)
    Rsize_mean = np.mean(Rsize)
    Zsize_mean = np.mean(Zsize)
    blob_deformation = Rsize_mean-Zsize_mean


    return delta_real_mean, Rsize_mean, Zsize_mean, blob_deformation


def calc_com_velocity(path=".", fname="rot_ell.curv.68.16.128.Ic_02.nc", tmax=-1, track_peak=False):
    
    """
   
    input:

    return:

    """

    
    n = collect("Ne", path=path, tind=[0, tmax], info=False)
    t_array = collect("t_array", path=path, tind=[0, tmax], info=False)
    wci = collect("Omega_ci", path=path, tind=[0, tmax], info=False)
    dt = (t_array[1] - t_array[0]) / wci

    nt = n.shape[0]
    nx = n.shape[1]
    ny = n.shape[2]
    nz = n.shape[3]

    if fname is not None:
        fdata = DataFile(fname)

        R = fdata.read("R")
        Z = fdata.read("Z")

    else:
        R = np.zeros((nx, ny, nz))
        Z = np.zeros((nx, ny, nz))
        rhos = collect('rho_s0', path=path, tind=[0, tmax])
        Rxy = collect("R0", path=path, info=False) * rhos
        dx = (collect('dx', path=path, tind=[0, tmax], info=False) * rhos * rhos / (Rxy))[0, 0]
        dz = (collect('dz', path=path, tind=[0, tmax], info=False) * Rxy)
        for i in np.arange(0, nx):
            for j in np.arange(0, ny):
                R[i, j, :] = dx * i
                for k in np.arange(0, nz):
                    Z[i, j, k] = dz * k

    max_ind = np.zeros((nt, ny))
    fwhd = np.zeros((nt, nx, ny, nz))
    xval = np.zeros((nt, ny), dtype='int')
    zval = np.zeros((nt, ny), dtype='int')
    xpeakval = np.zeros((nt, ny))
    zpeakval = np.zeros((nt, ny))
    Rpos = np.zeros((nt, ny))
    Zpos = np.zeros((nt, ny))
    pos = np.zeros((nt, ny))
    vr = np.zeros((nt, ny))
    vz = np.zeros((nt, ny))
    vtot = np.zeros((nt, ny))
    pos_fit = np.zeros((nt, ny))
    v_fit = np.zeros((nt, ny))
    Zposfit = np.zeros((nt, ny))
    RZposfit = np.zeros((nt, ny))

    for y in np.arange(0, ny):
        for t in np.arange(0, nt):

            data = n[t, :, y, :]
            nmax, nmin = np.amax((data[:, :])), np.amin((data[:, :]))
            data[data < (nmin + 0.368 * (nmax - nmin))] = 0
            fwhd[t, :, y, :] = data
            ntot = np.sum(data[:, :])
            zval_float = np.sum(np.sum(data[:, :], axis=0) * (np.arange(nz))) / ntot
            xval_float = np.sum(np.sum(data[:, :], axis=1) * (np.arange(nx))) / ntot

            xval[t, y] = int(np.round(xval_float))
            zval[t, y] = int(np.round(zval_float))

            xpos, zpos = np.where(data[:, :] == nmax)
            xpeakval[t, y] = xpos[0]
            zpeakval[t, y] = zpos[0]


            if track_peak:
                Rpos[t, y] = R[int(xpeakval[t, y]), y, int(zpeakval[t, y])]
                Zpos[t, y] = Z[int(xpeakval[t, y]), y, int(zpeakval[t, y])]
            else:
                Rpos[t, y] = R[xval[t, y], y, zval[t, y]]
                Zpos[t, y] = Z[xval[t, y], y, zval[t, y]]

        pos[:, y] = np.sqrt((Rpos[:, y] - Rpos[0, y]) ** 2)  
        z1 = np.polyfit(t_array[:], pos[:, y], 5)
        f = np.poly1d(z1)
        pos_fit[:, y] = f(t_array[:])

        t_cross = np.where(pos_fit[:, y] > pos[:, y])[0]
        t_cross = 0  # t_cross[0]

        pos_fit[:t_cross, y] = pos[:t_cross, y]

        z1 = np.polyfit(t_array[:], pos[:, y], 5)
        f = np.poly1d(z1)
        pos_fit[:, y] = f(t_array[:])


        v_fit[:, y] = calc.deriv(pos_fit[:, y]) / dt


        posunique, pos_index = np.unique(pos[:, y], return_index=True)
        pos_index = np.sort(pos_index)
        XX = np.vstack((t_array[:] ** 5, t_array[:] ** 4, t_array[:] ** 3, t_array[:] ** 2, t_array[:],
                        pos[pos_index[0], y] * np.ones_like(t_array[:]))).T

        pos_fit_no_offset = np.linalg.lstsq(XX[pos_index, :-2], pos[pos_index, y])[0]
        pos_fit[:, y] = np.dot(pos_fit_no_offset, XX[:, :-2].T)
        v_fit[:, y] = calc.deriv(pos_fit[:, y]) / dt



    return v_fit[:, 0], pos_fit[:, 0], pos[:, 0], Rpos[:, 0], Zpos[:, 0], t_cross
