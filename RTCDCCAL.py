#Written by Aaron Sahm and Adam Betemedhin 12/19/2017
#Requires installation of pySerial, pyVISA, and a configured GPIB connection
#Current version has been tested with a Keithley 2001, Sorensen DLM-40-15, National Instruments GPIB to USB interface
#Program on first run will ask for settings and write them to a file for future use
#Data collected is written to a file named "data.txt" in column separated by "space"
from __future__ import division
import serial
import time
from time import sleep
import datetime
import os
import visa
import socket
#DLM_host, DLM_port = '192.168.1.25', 9221
##global DLM_host, DLM_port
##DLM_host, DLM_port = '169.254.184.45', 9221
##steps = 5
##DLM_baudrate = 19200

def Setup_Keithley():
        print 'Setting up Keithley 2001...'
        rm = visa.ResourceManager()                             #Gather available devices on computer
        devices = str(rm.list_resources())                      #Gather available devices on computer
        gloc = devices.find('GPIB', 0, len(devices))            #Search for first GPIB device
        glocs = devices[gloc:len(devices)]                      #Store string of GPIB device till end of remaing devices
        gloce = glocs.find('INSTR', 0, len(glocs))              #Check for character location of first available INSTRUMENT on string
        k = rm.open_resource(devices[gloc:(gloc+gloce+5)])      #Use GPIB device and assume is Keithley 2001
        
        k.write('*RST')                                         #Reset
        sleep(1)
        k.write('*CLS')                                         #Clear
        sleep(1)
        k.write("SENS:FUNC 'VOLT:DC'")                          #Set to DC Voltage
        sleep(0.5)
        k.write('SENS:VOLT:DC:DIG 7.5; NPLC 10; AVER:COUN 5')   #Set to maximum resolution and integration with an average of 5 readings
        sleep(0.5)
        k.write('SENS:VOLT:DC:RANG 0.2')                        #Set to 200 mV range
        sleep(0.5)
        k.write(':INIT:CONT ON')                                #Set to continuous reading
        sleep(0.5)
        k.write(':FORM:ELEM READ')                              #Only read number output
        sleep(0.5)
        return k

def Serial_Method():
        k = Setup_Keithley()
        comport = 'COM' + str(ccomport)
        ser = serial.Serial()
        ser.baudrate = DLM_baudrate
        ser.port = comport
        ser.timeout = 1
        ser.open()

        if ser.isOpen():
            DATA=[]
            ser.write('*CLS' + '\r\n')
            sleep(1)

            ser.write('*RST' + '\r\n')
            sleep(1)

            ser.write('SOUR:VOLT:PROT ' + str(maxvolt) + '\r\n') #Set Over Voltage Protection
            sleep(1)

            ser.write('SOUR:CURR 0.0' + '\r\n')
            sleep(1)

            ser.write('SOUR:VOLT 1.0' + '\r\n') #Set Voltage Up to 1 Volt
            sleep(1)

            for i in range (0, steps+1):
                ser.write('SOUR:CURR ' + str(maxcurr/steps*i) + '\r\n')
                start = time.time()
                cset = maxcurr/steps*i
                sleep(0.5)
                ser.write('MEAS:VOLT?' + '\r\n')
                vread = ser.read(40)
                k.write('FETC?')
                st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                actcur = float(k.read())*shuntrate
                datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                if abs(actcur-(maxcurr/steps*i))>0.0003:
                    cset = maxcurr/steps*i-(actcur-(maxcurr/steps*i))
                    ser.write('SOUR:CURR ' + str(cset) + '\r\n')
                k.write('FETC?')
                st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                ser.write('MEAS:VOLT?' + '\r\n')
                vread = ser.read(40)
                actcur = float(k.read())*shuntrate
                datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                while (time.time()-start) < tdelay:
                    k.write('FETC?')
                    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
#                    ser.write('MEAS:VOLT?' + '\r\n')
#                    vread = ser.read(40)
                    actcur = float(k.read())*shuntrate
                    datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                    toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                    if abs(actcur-(maxcurr/steps*i))>0.0003:
                        if (actcur-(maxcurr/steps*i)) > 0:
                            cset = cset - 0.0001
                        else:
                            cset = cset + 0.0001
                        ser.write('SOUR:CURR ' + str(cset) + '\r\n')
                        sleep(0.5)
                        k.write('FETC?')
                        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
 #                       ser.write('MEAS:VOLT?' + '\r\n')
 #                       vread = ser.read(40)
                        actcur = float(k.read())*shuntrate
                        datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                        toscreen(st,(maxcurr/steps*i),cset,vread,actcur)

            ser.write('*RST' + '\r\n') #Reset DLM 40-15
            sleep(1)
            ser.write('SOUR:VOLT:PROT ' + str(maxvolt) + '\r\n') #Set Over Voltage Protection
            ser.write('OUTP:STAT OFF' + '\r\n') #Set output to off
            ser.close()
            writedata(DATA)
            print('Finished')
        else:
            print('Cannot connect to COM1')

        pass



def Ethernet_Method():
        k = Setup_Keithley()
        DATA=[]
        Read_Volt()
        Read_Curr()
        sleep(1)
        E_Write('*CLS')
        sleep(1)
        E_Write('*RST')
        sleep(1)
        E_Write('SOUR:VOLT:PROT ' + str(maxvolt))
        sleep(1)
        Set_Curr(0.0)
        sleep(1)
        Set_Volt(1.0)
        sleep(1)
        for i in range (0, steps+1):
                Set_Curr(maxcurr/steps*i)
                start = time.time()
                cset = maxcurr/steps*i
                sleep(1)
                vread = Read_Volt()
                k.write('FETC?')
                st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                actcur = float(k.read())*shuntrate
                datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                if abs(actcur-(maxcurr/steps*i))>0.0003:
                        cset = maxcurr/steps*i-(actcur-(maxcurr/steps*i))
                        Set_Curr(cset)
                k.write('FETC?')
                st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                actcur = float(k.read())*shuntrate
                vread = Read_Volt()
                datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                while (time.time()-start) < tdelay:
                        k.write('FETC?')
                        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        actcur = float(k.read())*shuntrate
                        vread = Read_Volt()
                        datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                        toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
                        if abs(actcur-(maxcurr/steps*i))>0.0003:
                                if (actcur-(maxcurr/steps*i)) > 0:
                                        cset = cset - 0.0001
                                else:
                                        cset = cset + 0.0001
                                Set_Curr(cset)
                                sleep(1)
                                k.write('FETC?')
                                st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                vread = Read_Volt()
                                actcur = float(k.read())*shuntrate
                                datacollect(DATA,st,(maxcurr/steps*i),cset,vread,actcur)
                                toscreen(st,(maxcurr/steps*i),cset,vread,actcur)
        E_Write('*RST')
        sleep(1)
        E_Write('SOUR:VOLT:PROT ' + str(maxvolt))
        E_Write('OUTP:STAT OFF')
        writedata(DATA)
        pass    

def toscreen(ltime,cstep,setc,cvolt,cur):
        print(ltime + ' Des.Cur= ' + str(cstep) + ' SetCur= ' + str(setc) + '  Volt= ' + str(float(cvolt)) + ' ActCurr= ' + str(cur))
        pass
        
def datacollect(DATA,ltime,cstep,setc,cvolt,cur):
        DATA.append(ltime + ' Des.Cur= ' + str(cstep) + ' SetCur= ' + str(setc) + '  Volt= ' + str(float(cvolt)) + ' ActCurr= ' + str(cur))
        return DATA

        
def writedata(tofile):
        if os.path.exists('data.txt'):
                method = 'a'
        else:
                method = 'w'
                
        datafile = open('data.txt', method)
        print 'Writing data to data.txt...'
        for item in tofile:
                datafile.write("%s\n" % item)
        datafile.close()

def Socket_Connect():
        print 'Connecting to DLM 40-15...'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DLM_host, DLM_port))
        return s

def Set_Volt(num):
        s = Socket_Connect()
        print 'Setting voltage to: ' + str(num)
        s.send('SOUR:VOLT '+str(num)+'\r\n')
        s.send('*WAI;:MEAS:VOLT?'+'\r\n')
        data = float(s.recv(1024))
        print 'Voltage set to: ' + str(data)
        pass


def Set_Curr(num):
        s = Socket_Connect()
        print 'Setting current to: ' + str(num)
        s.send('SOUR:CURR '+str(num)+'\r\n')
        s.send('*WAI;:MEAS:CURR?'+'\r\n')
        data = float(s.recv(1024))
        print 'Current set to: ' + str(data)
        pass


def Read_Volt():
        s = Socket_Connect()
        s.send('MEAS:VOLT?'+'\r\n')
        data = float(s.recv(1024))
        print 'Voltage set to: ' + str(data)
        return data


def Read_Curr():
        s = Socket_Connect()
        s.send('MEAS:CURR?'+'\r\n')
        data = float(s.recv(1024))
        print 'Current set to: ' + str(data)
        return data

def E_Write(string):
        s = Socket_Connect()
        s.send(string+'\r\n')
        pass

def Main():
        if connection_method == 1:
                Serial_Method()
        elif connection_method == 2:
                Ethernet_Method()
        else:
                print ('Incorrect Connection Method Selected')
                sys.exit(0)

        print 'Program Complete'
pass

try:
        from config import *
        configexists = 1
except ImportError:
        configexists = 0
if configexists == 1:
        print('Are the following settings correct? ')
        if connection_method == 1:
                print('DLM 40-15 connection is set to Serial')
                print('Using Com port: ' + str(ccomport))
                print('Using baud rate: ' + str(DLM_baudrate))
        else:
                print('DLM 40-15 connection is set to Ethernet')
                print('Using IP address: ' + str(DLM_host) + ' and Port: ' + str(DLM_port))
        print('Number of steps: ' + str(steps))
        print('Maximmum current: ' + str(maxcurr))
        print('Shunt calibration coefficient (Amps/V): ' + str(shuntrate))
        print('Delay time for each step: ' + str(tdelay))
        print('Over Voltage Protection Setting (Volts): ' + str(maxvolt))
        csettings = int(input('Enter 1 for "YES" and 2 for "NO" '))
        if csettings == 2:
                connection_method = int(input('Which connection method is the DLM-40-15 using? \nEnter 1 for serial.\nEnter 2 for Ethernet.\n(Integer only):'))
                if connection_method == 1:
                        ccomport = input('Which Com port is the DLM-40-15 connected to? (Integer only): ')
                        DLM_baudrate = input('What is the baud rate? (DLM typically 19200): ')
                else:
                        DLM_host = str(raw_input('What is the IP address for the DLM 40-15? '))
                        DLM_port = input('What is the port for the DLM40-15? ')
                maxcurr = input('What is the maximum current (Integer only)?: ')
                shuntrate = input('What is the calibrated current shunt calibration constant (amps/V)?: ')
                tdelay = input('What is the desired delay time for each step (in seconds, make larger than 5)?: ')
                steps = input('How many steps (set points) are there (5 is typical)?: ')
                maxvolt = input('What is the maximum allowable voltage (2 Volts typical)?: ')
                print('Writing settings to config.py...')
                file = open('config.py','w')
                file.write('#Configuration file for Calibration Code' + '\n')
                file.write('#DLM-40-15 Configuration settings' + '\n')
                if connection_method == 2:
                        file.write('global DLM_host, DLM_port' + '\n')
                        file.write('DLM_host, DLM_port = ' + "'" + DLM_host + "'" + ', ' + str(DLM_port) + '\n')
                        file.write('connection_method = 2   #1 for Serial and 2 for Ethernet' + '\n')
                else:
                        file.write('connection_method = 1   #1 for Serial and 2 for Ethernet' + '\n')
                        file.write('ccomport = 1  #comport for Serial connection' + '\n')
                        file.write('DLM_baudrate = ' + str(DLM_baudrate) + '\n')
                file.write('#Settings for DC Current Calibration' + '\n')
                file.write('steps = ' + str(steps) + '  #Number of current setpoints' + '\n')
                file.write('maxcurr = ' + str(maxcurr) + '  #Maximum DC current for test (Amps)' + '\n')
                file.write('shuntrate = ' + str(shuntrate) + '  #Current Shunt Calibration Coefficient (Amps/Volt)' + '\n')
                file.write('tdelay = ' + str(tdelay) + '  #Amount of time on each step (Seconds)' + '\n')
                file.write('maxvolt = ' + str(maxvolt) + '  #Over Voltage Protection (Volts)' + '\n')
                file.close()
else:
        csettings = 0
        connection_method = int(input('Which connection method is the DLM-40-15 using? \nEnter 1 for serial.\nEnter 2 for Ethernet.\n(Integer only):'))
        if connection_method == 1:
                ccomport = input('Which Com port is the DLM-40-15 connected to? (Integer only): ')
                DLM_baudrate = input('What is the baud rate? (DLM typically 19200): ')
        else:
                DLM_host = str(raw_input('What is the IP address for the DLM 40-15? '))
                DLM_port = input('What is the port for the DLM40-15? ')
        maxcurr = input('What is the maximum current (Integer only)?: ')
        shuntrate = input('What is the calibrated current shunt calibration constant (amps/V)?: ')
        tdelay = input('What is the desired delay time for each step (in seconds, make larger than 5)?: ')
        steps = input('How many steps (set points) are there (5 is typical)?: ')
        maxvolt = input('What is the maximum allowable voltage (2 Volts typical)?: ')
        print('Writing settings to config.py...')
        file = open('config.py','w')
        file.write('#Configuration file for Calibration Code' + '\n')
        file.write('#DLM-40-15 Configuration settings' + '\n')
        if connection_method == 2:
                file.write('global DLM_host, DLM_port' + '\n')
                file.write('DLM_host, DLM_port = ' + "'" + DLM_host + "'" + ', ' + str(DLM_port) + '\n')
                file.write('connection_method = 2   #1 for Serial and 2 for Ethernet' + '\n')
        else:
                file.write('connection_method = 1   #1 for Serial and 2 for Ethernet' + '\n')
                file.write('ccomport = 1  #comport for Serial connection' + '\n')
                file.write('DLM_baudrate = ' + str(DLM_baudrate) + '\n')
        file.write('#Settings for DC Current Calibration' + '\n')
        file.write('steps = ' + str(steps) + '  #Number of current setpoints' + '\n')
        file.write('maxcurr = ' + str(maxcurr) + '  #Maximum DC current for test (Amps)' + '\n')
        file.write('shuntrate = ' + str(shuntrate) + '  #Current Shunt Calibration Coefficient (Amps/Volt)' + '\n')
        file.write('tdelay = ' + str(tdelay) + '  #Amount of time on each step (Seconds)' + '\n')
        file.write('maxvolt = ' + str(maxvolt) + '  #Over Voltage Protection (Volts)' + '\n')
        file.close()
Main()


