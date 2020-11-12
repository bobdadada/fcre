# -*- coding: utf-8 -*-
"""
Created on Wed Okt 10 11:11:49 2018

@author: Daniel Schiessl

------------------------------------------------------------------------------------------------
(c) COPYRIGHT 2018 by attocube systems AG, Germany. All rights reserved.

This module shall be a starting point for everyone working with Python and wanting
to integrate an AMC100 to their setup. For any suggestions on code optimization
or already modified code please contact Daniel Schiessl:
daniel.schiessl@attocube.com

HISTORY:
Date Author Description
2017-07-20 DSc created
2018-08-24 DSc updated for usage in Python
2018-09-26 JH added Function Decsriptions
yyyy-mm-dd ... ...
------------------------------------------------------------------------------------------------

"""

import socket
import json

TCP_PORT = 9090
BUFFER_SIZE = 100

def connect(IP):
    """
        Initializes and connects the selected AMC device.
    Parameters
    ----------
    IP : String
        Address of the device to connect
    """
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.settimeout(3)
    tcp.connect((IP, TCP_PORT))
    return tcp

def close(tcp):
    """
        Closes the connection to the device.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    """
    tcp.close()
    
def getLockStatus(tcp):
    """
        This function gets information whether the device is locked and if access is authorized.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    authorized : Bln
       indicates if access is granted
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "getLockStatus", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0], response['result'][1]

def lock(tcp, password):
    """
        This function locks the device, so the calling of functions is only possible with valid password.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    password
        password for locking the Device
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    password = str(password)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"lock","params":["'+password+'"],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def grantAccess(tcp, password):
    """
        This function requests access to a locked device, so all functions can be called after entering the correct password. Otherwise, each function creates an error.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    password
        password for locking the Device
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    password = str(password)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"grantAccess","params":["'+password+'"],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]
    
def errorNumberToString(tcp, language, errorNumber):
    """
        This function “translates” the error code into an error text and adds it to the error out cluster.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    language :Int32
        Language of error massage
    errorNumber : Int32
        error code to translate
    Returns
    -------
    error : String
       error message
    """
    language = str(language)
    errorNumber = str(errorNumber)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.system.errorNumberToString","params":['+ language +','+errorNumber+'],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return response['result'][0]

def unlock(tcp):
    """
        This function unlocks the device, so it will not be necessary to execute the grantAccess function to run any VI.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "unlock", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def setOutput(tcp, axis, enable):
    """
        This function sets the status of the output relays of the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    enable : Bln
        Switches the output relais
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false.lower() # convert booleans to lower case True --> true / False --> false
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlOutput", "params": ['+axis+','+enable+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getOutput(tcp, axis):
    """
        This function gets the status of the output relays of the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    enable : Bln
       Status of Output relais
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlOutput", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setAmplitude(tcp, axis, amplitude):
    """
        Controls the amplitude of the actuator signal.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    amplitude : Int32
        Amplitude in mV
    Returns
    ----------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    amplitude = str(amplitude)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlAmplitude", "params": ['+axis+','+amplitude+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getAmplitude(tcp, axis):
    """
        Get Status of the amplitude of the actuator signal.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    amplitude : Int32
        Amplitude in mV
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlAmplitude", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setFrequency(tcp, axis, frequency):
    """
        Controls the frequency of the actuator signal.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    frequency : Int32
        Frequency in mHz
    Returns
    -------
    errorNumber : Int32
       No error = 0        
    """
    axis = str(axis)
    frequency = str(frequency) # Frequency in mHz
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlFrequency", "params": ['+axis+','+frequency+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getFrequency(tcp, axis):
    """
        Get Status of the frequency of the actuator signal.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    frequency : Int32
        Frequency in mHz
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlFrequency", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setActorSelection(tcp, axis, name):
    """
        This function sets the name for the positioner on the selected axis.
    Parameters
    ----------
    axis : Int32
       Number of the axis to be used [0..2]
    name : String
        name of the positioner
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    name = str(name)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.control.setActorParametersByname","params": ['+ axis +',"'+ name+'"],"id":"3"}', 'utf-8')) # name needs the "" additionally!
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getActorname(tcp, axis):
    """
        This function gets the name of the positioner of the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    actor name : String
       name of the positioner
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.control.getActorParametersActorname","params":['+ axis +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def getActorType(tcp, axis):
    """
        This function gets the type of the positioner of the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    positioner type : String
       type of the positioner
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.control.getActorType","params":['+ axis +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]# 0 = linear , 1 = rotator,  2 = goniometer

def setReset(tcp, axis):
    """
        Resets the actual position to zero and marks the reference position as invalid.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setReset", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def setMove(tcp, axis, enable):
    """
        Controls the approach of the actor to the target position
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    enable : Bln
        True: enable actor approach towards target position
        Falsee: disable actor approach towards target position
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlMove", "params": ['+axis+','+enable+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getMove(tcp, axis):
    """
        status of the approach of the actor to the target position
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be monitored [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    movingStatus : Int32
       0 = not moving; 1 = moving 
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlMove", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0], response['result'][1]

def setNSteps(tcp, axis, backward, n):
    """
        triggers N steps in desired direction.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    backward : Bln
        Selects the desired direction.
    N : Int32
        Number of steps
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    backward = str(backward).lower() # convert booleans to lower case True --> true / False --> false ;
    n = str(n)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.setNSteps", "params": ['+axis+','+backward+','+n+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def setSingleStep(tcp, axis, direction):
    """
        triggers one step in desired direction.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    direction : Bln
        direction of movement
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    direction = str(direction).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.setNSteps", "params": ['+axis+','+direction+',1], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getNSteps(tcp, axis):
    """
        gets number of steps set
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    N : Int32
        Number of steps
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getNSteps", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0], response['result'][1]

def setContinuousFwd(tcp, axis, enable):
    """
        set a continuous movement on the selected axis in positive direction
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    enable : Bln
        True: enable continuous movement in forward direction
        False = disable continuous movement in forward direction
    Returns
    -------
    errorNumber : Int32
       No error = 0
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.move.setControlContinousFwd","params":['+axis+','+enable+'],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getContinuousFwd(tcp, axis):
    """
        get information about continuous movement on the selected axis in positive direction
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    statusContinuousFwd : Bln
        True: continuous movement in forward direction enabled
        False = disable continuous movement in forward disabled
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getControlContinousFwd", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setContinuousBkwd(tcp, axis, enable):
    """
        set a continuous movement on the selected axis in negative direction
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    enable : Bln
        True: enable continuous movement in forward direction
        False = disable continuous movement in forward direction
    Returns
    -------
    errorNumber : Int32
       No error = 0       
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.move.setControlContinousBkwd","params":['+axis+','+ enable +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return response['result'][0]

def getContinuousBkwd(tcp, axis):
    """
        get information about continuous movement on the selected axis in negative direction
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    statusContinuousFwd : Bln
        True: continuous movement in forward direction enabled
        False = disable continuous movement in forward disabled
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getControlContinousBkwd", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setTargetPosition(tcp, axis, target):
    """
        sets the target position for the movement on the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    target : Int32
        target position in nm
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    target = str(target)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.setControlTargetPosition", "params": ['+axis+','+target+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getTargetPosition(tcp, axis):
    """
        get the target position for the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
        Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0    
    target : Int32
        target position in nm  
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getControlTargetPosition", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getStatusReference(tcp, axis):
    """
       gets information about the status of the reference position
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    status : Bln
        True: Reference position is valid
        False: Reference position is invalid 
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusReference", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getStatusMoving(tcp, axis):
    """
        get information about the status of the stage output
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    status : Int32
       0: idle (no movement commands for positioner pending)
       1: moving (positioner actively driven to target position)
       2: pending (positioner in target range and not actively driven)
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusMoving", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getStatusConnected(tcp, axis):
    """
    This function gets information about the connection status of the selected axis’ positioner.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    conected : Bln
       true: positioner electrically connected to controller false: positioner not electrically connected to controller
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusConnected", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getReferencePosition(tcp, axis):
    """
       This function gets the reference position of the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    reference : Int32
       reference position in nm
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getReferencePosition", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getPosition(tcp, axis):
    """
        This function gets the current position of the positioner on the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    position : Int32
       positioner’s position in nm
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getPosition", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setReferenceAutoUpdate(tcp, axis, enable):
    """
        This function sets the status of whether the reference position is updated when the reference mark is hit.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    enable : Bln
        true: update reference position every time the reference mark is hit false: update reference position just once when the reference mark is hit for the first time, ignore further hits
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlReferenceAutoUpdate", "params": ['+axis+','+enable+ '], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getReferenceAutoUpdate(tcp, axis):
    """
        This function gets the status of whether the reference position is updated when the reference mark is hit.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
     enable : Bln
        true: update reference position every time the reference mark is hit false: update reference position just once when the reference mark is hit for the first time, ignore further hits
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlReferenceAutoUpdate", "params": ['+axis+ '], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setAutoReset(tcp, axis, enable):
    """
        This function resets the position every time the reference position is detected.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    enable : Bln
        true: reset position every time the reference position is detected false: do not reset the position every time the reference position is detected
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlAutoReset", "params": ['+axis+','+ enable +'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    #if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getAutoReset(tcp, axis):
    """
        This function gets the Status if the controller resets the position every time the reference position is detected.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    enable : Bln
        true: reset position every time the reference position is detected false: do not reset the position every time the reference position is detected
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlAutoReset", "params": ['+axis+'], "id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setTargetRange(tcp, axis, Range):
    """
        set the range around the target position in which the flag "In Target Range" becomes active.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Range : Int32
       target range in nm
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    Range = str(Range)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlTargetRange", "params": ['+axis+','+ Range+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getTargetRange(tcp, axis):
    """
       get the range around the target position in which the flag "In Target Range" becomes active.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    Range : Int32
       target range in nm
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlTargetRange", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getStatusTargetRange(tcp, axis):
    """
       get information about whether the selected axis’ positioner is in target range or not
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    in target range : Bln
        True: positioner is within target range
        False: positioner is not within target range
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusTargetRange", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getFirmwareVersion(tcp):
    """
        This function gets the version number of the controller’s firmware.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    version : String
       firmware version number
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.getFirmwareVersion", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def getFpgaVersion(tcp):
    """
        This function gets the version number of the controller’s FPGA.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    version : String
       FPGA version number
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.description.getFpgaVersion", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def rebootSystem(tcp):
    """
        This function reboots the device.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.system.rebootSystem","params":[],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return response['result'][0]

def factoryReset(tcp):
    """
        This function resets the device to the factory settings when it’s booted the next time.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.system.factoryReset","params":[],"id":3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return response['result'][0]

def getMAC(tcp):
    """
        This function gets the MAC address of the device.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    mac : String
       MAC address
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.getMacAddress", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def getIPAddress(tcp):
    """
        This function gets the IP address of the device.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    mac : String
       MAC address
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.network.getIpAddress", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def getDeviceType(tcp):
    """
        This function gets the device type based on its EEPROM configuration.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    type : String
       type of the device
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.description.getDeviceType", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def getSN(tcp):
    """
        This function gets the device’s serial number.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    SN : String
       Serial number
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.getSerialNumber", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def getDevicename(tcp):
    """
        This function gets the device’s name.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    Devicename : String
       get device name
    """
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.getDevicename", "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def setDevicename(tcp, devicename):
    """
        This function sets the device’s name.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Devicename : String
       set device name
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    Devicename = str(devicename)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.system.setDevicename", "params": ["'+devicename+'"],  "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getStatusEotFwd(tcp, axis):
    """
        This function gets the status of the end of travel detection on the selected axis in forward direction.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    EotDetected : Bln
       true: end of travel in forward direction detected false: end of travel in forward direction not detected
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusEotFwd", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def getStatusEotBkwd(tcp, axis):
    """
        This function gets the status of the end of travel detection on the selected axis in backward direction.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    EotDetected : Bln
       true: end of travel in forward direction detected false: end of travel in forward direction not detected
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.status.getStatusEotBkwd", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setEotOutputDeactive(tcp, axis, enable):
    """
        This function sets he output applied to the selected axis on the end of travel.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    enable : Bln
        true: deactivate output on end of travel false: keep output active on end of travel
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.setControlEotOutputDeactive", "params": ['+axis+','+enable+ '], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getEotOutputDeactive(tcp, axis):
    """
        This function gets the output applied to the selected axis on the end of travel.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    enable : Bln
        true: deactivate output on end of travel false: keep output active on end of travel
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.move.getControlEotOutputDeactive", "params": ['+axis+ '], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]

def setFixOutputVoltage(tcp, axis, voltage):
    """
        This function sets the DC level output of the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Voltage : Int32
        DC output in mV
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    voltage = str(voltage)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.setControlFixOutputVoltage", "params": ['+axis+','+ voltage+  '], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getFixOutputVoltage(tcp, axis):
    """
        This function gets the DC level output of the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    Voltage : Int32
        DC output in mV
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc": "2.0", "method": "com.attocube.amc.control.getControlFixOutputVoltage", "params": ['+axis+'], "id": 3}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return  response['result'][0], response['result'][1]


def getPositionersList(tcp):
    """
        This function gets a list of the positioners connected to the device.
    Parameters
    -------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    list : String
       name of Positioner
    listSize : Int32
       Size of List
    """
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.description.getPositionersList","params":[],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    return  response['result'][0]

def setAQuadBInResolution(tcp, axis, resolution):
    """
        This function sets the real time input resolution for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    resolution : Int32
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    resolution = str(resolution)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setControlAQuadBInResolution","params":['+ axis +','+ resolution +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtin.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getAQuadBInResolution(tcp, axis):
    """
        This function gets the real time input resolution for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    resolution : Int32
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getControlAQuadBInResolution","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setAQuadBOut(tcp, axis, enable):
    """
        This function enables the real time output for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    enable : bln
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.setControlAQuadBOut","params":['+ axis +','+ enable +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtout.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getAQuadBOut(tcp, axis):
    """
        This function gets the status of the real time output for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    enable : Int32
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.getControlAQuadBOut","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setAQuadBOutResolution(tcp, axis, resolution):
    """
        This function sets the real time output resolution for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    resolution : Int32
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    resolution = str(resolution)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.setControlAQuadBOutResolution","params":['+ axis +','+ resolution +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtout.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getAQuadBOutResolution(tcp, axis):
    """
        This function gets the real time output resolution for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    resolution : Int32
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.getControlAQuadBOutResolution","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setAQuadBOutclock(tcp, axis, clock):
    """
        This function sets the real time output clock for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    clock : Int32
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    clock = str(clock)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.setControlAQuadBOutclock","params":['+ axis +','+ clock +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtout.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getAQuadBOutclock(tcp, axis):
    """
        This function gets the real time output clock for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    clock : Int32
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.getControlAQuadBOutclock","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setRtOutsignalMode(tcp, signalMode):
    """
        This function sets the real time output Signal mode for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    signalMode : Int32
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    signalMode = str(signalMode)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.setRtOutsignalMode","params":['+ signalMode +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtout.apply","params":[0]}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getRtOutsignalMode(tcp):
    """
        This function gets the real time output Signal mode for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    SinalMode : Int32
    """
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtout.getRtOutsignalMode","params":[0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setRealTimeInMode(tcp, axis, rtMode):
    """
        This function sets the real time input mode for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    rtMode : Int32
        0: Aquadb (LVTTL) 1: AquadB (LVDS) 8: Stepper (LVTTL) 9: Stepper(LVDS) 0: Trigger (LVTTL 11: Trigger (LVDS) 15: disable
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    rtMode = str(rtMode)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setRealTimeInMode","params":['+ axis +','+ rtMode +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtin.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getRealTimeInMode(tcp, axis):
    """
        This function gets the real time input mode for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    rtMode : Int32
        0: Aquadb (LVTTL) 1: AquadB (LVDS) 8: Stepper (LVTTL) 9: Stepper(LVDS) 0: Trigger (LVTTL 11: Trigger (LVDS) 15: disable
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getRealTimeInMode","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0],convert_ModeNo2string(response['result'][1])

def convert_ModeNo2string(rtMode):
    """
        converts Numbers to names
    Parameters
    ----------
    rtMode : Int32
        0: Aquadb (LVTTL) 1: AquadB (LVDS) 8: Stepper (LVTTL) 9: Stepper(LVDS) 0: Trigger (LVTTL 11: Trigger (LVDS) 15: disable
    Returns
    -------
    Mode : String
       0: Aquadb (LVTTL) 1: AquadB (LVDS) 8: Stepper (LVTTL) 9: Stepper(LVDS) 0: Trigger (LVTTL 11: Trigger (LVDS) 15: disable


    """
    if rtMode == 0: Mode = 'AquadB_LVTTL'
    elif rtMode == 1: Mode = 'AquadB_LVDS'
    elif rtMode == 2: Mode = 'HSSL_LVTTL' # currently not supported
    elif rtMode == 3: Mode = 'HSSL_LVDS' # currently not supported
    elif rtMode == 4: Mode = 'SPI_LVTTL' # currently not supported
    elif rtMode == 8: Mode = 'STEPPER_LVTTL'
    elif rtMode == 9: Mode = 'STEPPER_LVDS'
    elif rtMode == 10: Mode = 'TRIGGER_LVTTL'
    elif rtMode == 11: Mode = 'TRIGGER_LVDS'
    elif rtMode == 15: Mode = 'OFF'
    else: Mode = 'unknown'
    return Mode

def setRealTimeInFeedbackLoopMode(tcp, axis, rtMode):
    """
        This function sets the real time input loop mode for the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    rtMode : Int32
       0: open-loop
       1: closed-loop
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    rtMode = str(rtMode)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setRealTimeInFeedbackLoopMode","params":['+ axis +','+ rtMode +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    return response['result'][0]

def getRealTimeInFeedbackLoopMode(tcp, axis):
    """
        This function gets the real time input loop mode for the selected axis
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    rtMode : Int32
       0: open-loop
       1: closed-loop
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getRealTimeInFeedbackLoopMode","params":['+ axis +',0],"id":"3"}', 'utf-8')) # True gets the temp value (if no apply has been sent)
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]); return_value = 'ERROR'
    else:
        if response['result'][1] == 0: return_value = 'open-loop'
        elif response['result'][1] == 1: return_value = 'closed-loop'
    return return_value

def setRealtimeInputChangePerPulse(tcp, axis, change):
    """
        This function sets the real time input change per Pulse for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    change : Int32
        change per pulse in nm – maximum 1,000,000 nm
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    change = str(change)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setRealTimeInChangePerPulse","params":['+ axis +','+ change +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtin.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getRealtimeInputChangePerPulse(tcp, axis):
    """
        This function gets the real time input change per Pulse for the selected axis.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    change : Int32
        change per pulse in nm – maximum 1,000,000 nm
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getRealTimeInChangePerPulse","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setRealtimeInputStepsPerPulse(tcp, axis, steps):
    """
        This function sets the steps per pulse for the selected axis under real time input in closed-loop mode.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    steps : Int32
        number of steps per pulse – maximum 10,000 steps
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    steps = str(steps)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setRealTimeInStepsPerPulse","params":['+ axis +','+ steps +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtin.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getRealtimeInputStepsPerPulse(tcp, axis):
    """
        This function gets the steps per pulse for the selected axis under real time input in closed-loop mode.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    steps : Int32
        number of steps per pulse – maximum 10,000 steps
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getRealTimeInStepsPerPulse","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def setRealtimeInputMove(tcp, axis, enable):
    """
        This function sets the status for real time input on the selected axis in closed-loop mode.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    enable : bln
        true: enable movements
        false: disable movements
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    """
    axis = str(axis)
    enable = str(enable).lower() # convert booleans to lower case True --> true / False --> false ;
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.setControlMoveGPIO","params":['+ axis +','+ enable +'],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null'): print_ERROR(tcp,response['result'][0]) # if error print the error
    else: tcp.send(bytes('{"id":1,"jsonrpc":"2.0","method":"com.attocube.amc.rtin.apply","params":['+ axis +']}', 'utf-8')) # if no error s apply message
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response  # get the answer from the apply message
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0]) # and check the answer from the apply message
    return response['result'][0]

def getRealtimeInputMove(tcp, axis):
    """
        This function gets the status for real time input on the selected axis in closed-loop mode.
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    axis : Int32
       Number of the axis to be used [0..2]
    Returns
    -------
    errorNumber : Int32
       No error = 0      
    enable : Int32
        true: enable movements
        false: disable movements
    """
    axis = str(axis)
    tcp.send(bytes('{"jsonrpc":"2.0","method":"com.attocube.amc.rtin.getControlMoveGPIO","params":['+ axis +',0],"id":"3"}', 'utf-8'))
    response = json.loads(getJSONresponse(tcp)) # get and parse JSON response
    if (response['result'][0] != 0 and response['result'][0] != 'null') == True: print_ERROR(tcp,response['result'][0])
    return  response['result'][0], response['result'][1]

def getJSONresponse(tcp):
    """
        This Funktion gets and parses the JSON response
    Parameters
    ----------
    tcp : Int32
        TCP/IP connection ID
    Returns
    -------
    response : Index Table
       Table of Values
    """
    response = ''
    remainder = ''
    while '\r\n' not in response: # receive data as long as there is no CRLF in data
        response += tcp.recv(100).decode("utf-8") # concatenate new data to already received data
    i = response.rfind("\r\n") # find position index of CRLF
    response, remainder = response[:i+2], response[i+2:] # split response at CRLF
    if remainder != '': print('Warning, there is some ignored data after CRLF: ' + str(remainder))
    #print('response: ' + str(response)) # show data before CRLF for bedugging
    return response #, remainder

def print_ERROR(tcp,errorNumber):
    """
    converts the errorNumber into an error string an prints it to the console
    Parameters
    ----------
    errorNumber : int32
    """
    errorNumber = str(errorNumber)
    print("Error! " + str(errorNumberToString(tcp,0, errorNumber)))