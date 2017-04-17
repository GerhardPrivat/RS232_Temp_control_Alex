# +-+-+- PROGRAM FOR OSX +-+-+-
import numpy as np
import matplotlib.pyplot as plt
import serial
import pyvisa as visa
import time
import datetime
import os
import threading
import multiprocessing
import ctypes
import sys
import operator 
import warnings
import matplotlib.cbook

from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator

warnings.filterwarnings("ignore","Item size computed from the PEP 3118 buffer format string does not match the actual item size.")
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)




# +-+-+- CHILD PROCESS +-+-+-
# ---------------------------
# The child process takes care of communicating with the temperature controller and user input.
# Both actions are distributed on two different threads.
def readingwriting(timeint, countmax, newstdin, continuous, datalist, flag, a, b, c):
    
    # -- SERIAL CONNECTION --
    #ser1 = serial.Serial(
    #    port = "/dev/tty.usbserial-FTYNZXW4",
    #    baudrate = 19200,
    #    parity = serial.PARITY_NONE,
    #    stopbits = serial.STOPBITS_ONE,
    #    bytesize = serial.EIGHTBITS,
    #    xonxoff=True,
    #    timeout=1
    #)
    
    # -- GPIB CONNECTION --
    rm = visa.ResourceManager()
    multimeter = rm.open_resource("GPIB0::11::INSTR")
    
    
    # Function that is executed in the first thread. But only if the continuous variable is set to "n" at the beginning in the main process.
    # This function (thread) runs forever except the flag is set. Since the size of the storage array is fixed, the oldest data points
    # are going to be deleted.
    def recordingresistance1(timeint, countmax, multimeter, datalist, a, b, c):
        
        count = 0
        starttime1 = time.time()
        
        timearray = np.zeros(countmax,dtype="float")
        resistancearray = np.zeros(countmax,dtype="float")
        temperaturearray = np.zeros(countmax,dtype="float")
        timestamparray = np.zeros(countmax,dtype="float")

        while True:
            if (flag.value == 0):
                starttime2 = time.time()

                #ser.write(":FETC?\r\n")
                #resis = ser.readline()
                #print resis[1:len(resis)-3]
                resis = multimeter.query(":FETC?")
                try:
                    #resis = float(resis[1:len(resis)-3])
                    resis = float(resis)
                    if (resis > 1e10):
                        resis = np.nan
                except:
                    print "\n    - Wrong readout: ",resis
                    resis = np.nan
	    
                if (count < countmax):
                    timearray[count] = time.time()-starttime1
                    resistancearray[count] = resis
                    temperaturearray[count] = f(resis,a,b,c)
               	    timestamparray[count] = starttime2 
                    count += 1
                        
                else:
                    timearray = np.roll(timearray,len(timearray)-1)
                    resistancearray = np.roll(resistancearray,len(resistancearray)-1)
                    temperaturearray = np.roll(temperaturearray,len(temperaturearray)-1)
                    timestamparray = np.roll(timestamparray,len(timestamparray)-1)
                    timearray[countmax-1] = time.time()-starttime1
                    resistancearray[countmax-1] = resis
                    temperaturearray[contmax-1] = f(resis,a,b,c)
                    timestamparray[countmax-1] = starttime2
                
                datalist.append([timearray,resistancearray,temperaturearray,timestamparray])
                
                if (count >= 3):
                    del datalist[0]
                
                try:
                    time.sleep(timeint-time.time()+starttime2)
                except:
                    time.sleep(2*timeint-time.time()+starttime2)
            else:
                break
    
    
    # Function that is executed in the first thread. But only if the continuous variable is set to "y" at the beginning in the main process.
    # This function (thread) stops when the storage array is completely filled. No data points are going to be deleted.
    # This function (thread) can also be stopped by entering "exit".
    def recordingresistance2(timeint, countmax, multimeter, datalist, a, b, c):
        
        count = 0
        starttime1 = time.time()
        
        timearray = np.zeros(countmax,dtype="float")
        resistancearray = np.zeros(countmax,dtype="float")
        temperaturearray = np.zeros(countmax,dtype="float")
        timestamparray = np.zeros(countmax,dtype="float")

        while True:
            if (flag.value == 0):
                starttime2 = time.time()
    
                #ser.write(":FETC?\r\n")
                #resis = ser.readline()
                #print resis[1:len(resis)-3]
                resis = multimeter.query(":FETC?")
                try:
                    #resis = float(resis[1:len(resis)-3])
                    resis = float(resis)
                    if (resis > 1e10):
                        resis = np.nan  
                except:
                    print "\n    - Wrong readout: ",resis
                    resis = np.nan
		
                if (count < countmax):
                    timearray[count] = time.time()-starttime1
                    resistancearray[count] = resis
                    temperaturearray[count] = f(resis,a,b,c)
                    timestamparray[count] = starttime2

                    count += 1
                        
                else:
                    flag.value = 1
                    break
                
                datalist.append([timearray,resistancearray,temperaturearray,timestamparray])
                
                if (count >= 3):
                    del datalist[0]
                    
                try:
                    time.sleep(timeint-time.time()+starttime2)
                except:
                    time.sleep(2*timeint-time.time()+starttime2)
            else:
                break
        
        
    # Function that is executed in the second thread. THe function waits for user input. One can either enter a new set temperature or the exit
    # command. 
    def exitfunction(newstdin):
    
        newstdinfile = os.fdopen(os.dup(newstdin))
    
        while True:
            print("   - End acquisition with \"exit\": "),
            exit_checkout = newstdinfile.readline()
            exit_checkout = exit_checkout[:len(exit_checkout)-1]
                        
            if (exit_checkout == "exit"):
                flag.value = 1
                newstdinfile.close()
                break
            else:
                continue




    # -- ACTUAL CHILD PROCESS --        
    # Start both actions in tow different threads:
    if (continuous == "n"):
        thread1 = threading.Thread(target=recordingresistance1, args=(timeint,countmax,multimeter,datalist,a,b,c))
        thread2 = threading.Thread(target=exitfunction, args=(newstdin,))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()

    else:
        thread1 = threading.Thread(target=recordingresistance2, args=(timeint,countmax,multimeter,datalist,a,b,c))
        thread2 = threading.Thread(target=exitfunction, args=(newstdin,))
        thread2.daemon = True
            
        thread1.start()
        thread2.start()
    
        thread1.join()
        
    #ser1.close()
    multimeter.close()





# +-+-+- MAIN PROCESS +-+-+-
# --------------------------
# The main process is solely for plotting the read data.

# -- FUNCTIONS FOR MAIN PROCESS --
def timeconvert(x):
    if (x[len(x)-1] == "s"):
        x = float(x[:len(x)-1])
        return x
    
    if (x[len(x)-1] == "m"):
        x = float(x[:len(x)-1])*60
        return x
    
    if (x[len(x)-1] == "h"):
        x = float(x[:len(x)-1])*3600
        return x
    
def cm2inch(value):
    return value/2.54

def formatfunc(x, pos):
    return "%.2f" %(x/1e3)

def f(x,a,b,c):
    return (a+b*np.log(x)+c*np.log(x))**(-1)


# -- ACTUAL MAIN PROCESS --
if __name__ == '__main__':
    os.system("cls")
    print "\n\n\n"
    print "-------------------------------------------"
    print "--------- RESISTANCE ACQUISITION ----------"
    print "-------------------------------------------"
    print "\n\n\n"
    
    print " + Reading fit parameters..."
    a,b,c = np.genfromtxt("Steinhart-Hart-Equation_Fit_Paramters.txt",dtype="float",unpack=True)
    
    timeint = "1s"#raw_input("\n + Time-intervals (#m or #s; at least 0.08s): ")
    timeint = timeconvert(timeint)
    
    timemax = raw_input("\n + Maximal time plotted (#h, #m or #s): ")
    timemax = timeconvert(timemax)
    
    countmax = int(timemax/timeint)
    
    alldata = raw_input(" + Show all data (y/n): ")
    if (alldata == "n"):
	    plottimemax = raw_input(" + Maximal time shown in plot (#h, #m or #s): ")
	    plottimemax = timeconvert(plottimemax)
    
    continuous = raw_input(" + Stop recording after maximal time elapsed (y/n) ?: ")
    
    plotlimit = 1.#float(raw_input(" + Plotlimits: "))
    Rplotlimit = 1000.
    Tplotlimit = 5.
    
    datamanager = multiprocessing.Manager()
    datalist = datamanager.list()
    
    flag = multiprocessing.Value(ctypes.c_int, 0)
    
    
    #if (data_np.nbytes/1e6 > 1000):
    #    print "\n + Storage array greater than 1GB!"
    #else:
    #    print "\n + "+str(data_np.nbytes/1e6)+"MB storage array and "+str(countmax)+" values.\n"
    #
    print " + End acquisition with \"exit\": "
    
    
    newstdin = sys.stdin.fileno()
    
    # Start the child process:
    readingwritingprocess = multiprocessing.Process(target=readingwriting, args=(timeint,countmax,newstdin,continuous,datalist,flag,a,b,c))
    readingwritingprocess.start()
    
    
    plt.ion()
    fig = plt.figure(tight_layout=True,figsize=(cm2inch(40),cm2inch(15)))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)
    ax1.set_xlabel("Time [s]")
    ax2.set_xlabel("Time [s]")
    ax1.set_ylabel("Temperature [C]")
    ax2.set_ylabel("Resistance [kOhm]")
    ax2.yaxis.set_major_formatter(FuncFormatter(formatfunc))
    ax1.grid(True)
    ax2.grid(True)
    
    line1, = ax1.plot([],[],linewidth=2,color="red")
    line2, = ax2.plot([],[],linewidth=2,color="blue")
    
    plotstart = 0
    while True:
        try:
            data = datalist[-1]
            if (flag.value == 0):
                try:
                    count = np.where(data[0]==0)[0][0]
                    if (count == 0): count = np.where(data[0]==0)[0][1]
                except:
                    count = countmax
            
                if (alldata == "y"):
                    line1.set_xdata(data[0][:count])
                    line1.set_ydata(data[2][:count])
                    line2.set_xdata(data[0][:count])
                    line2.set_ydata(data[1][:count])
                    if (count != 0):
                        ax1.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0][:count])+plotlimit)
                        ax1.set_ylim(np.nanmin(data[2][:count])-Tplotlimit,np.nanmax(data[2][:count])+Tplotlimit)
                        ax2.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0][:count])+plotlimit)
                        ax2.set_ylim(np.nanmin(data[1][:count])-Rplotlimit,np.nanmax(data[1][:count])+Rplotlimit)
            
                else:
                    if (np.amax(data[0]) >= plottimemax):
                        plotstart = int(abs(count-plottimemax/timeint))
                    else:
                        plotstart = 0

                    line1.set_xdata(data[0][plotstart:count])
                    line1.set_ydata(data[2][plotstart:count])
                    line2.set_xdata(data[0][plotstart:count])
                    line2.set_ydata(data[1][plotstart:count])
                    if (count != 0):
                        ax1.set_xlim(np.nanmin(data[0][plotstart:count])-plotlimit,np.nanmax(data[0][plotstart:count])+plotlimit)
                        ax1.set_ylim(np.nanmin(data[2][plotstart:count])-Tplotlimit,np.nanmax(data[2][plotstart:count])+Tplotlimit)
                        ax2.set_xlim(np.nanmin(data[0][plotstart:count])-plotlimit,np.nanmax(data[0][plotstart:count])+plotlimit)
                        ax2.set_ylim(np.nanmin(data[1][plotstart:count])-Rplotlimit,np.nanmax(data[1][plotstart:count])+Rplotlimit)
                    #else:
                        #line1.set_xdata(data[0][:count])
                        #line1.set_ydata(data[2][:count])
                        #line2.set_xdata(data[0][:count])
                        #line2.set_ydata(data[1][:count])
                        #if (count != 0):
                            #ax1.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0])+plotlimit)
                            #ax1.set_ylim(np.nanmin(data[2][:count])-Tplotlimit,np.nanmax(data[2])+Tplotlimit)
                            #ax2.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0])+plotlimit)
                            #ax2.set_ylim(np.nanmin(data[1][:count])-Rplotlimit,np.nanmax(data[1])+Rplotlimit)			
        
                try:
                    temperatureannotation.remove()
                    averagetemperatureannotation.remove()
                    temperaturestandarddeviationannotation.remove()
                    resistanceannotation.remove()
                    averageresistanceannotation.remove()
                    resistancestandarddeviationannotation.remove()
                except:
                    pass
            
                #temperatureannotation = ax1.annotate(r"$T = \SI{%.3f}{\degreeCelsius}$" %data[2][count-1], xy=(0.5,0.9), xycoords="axes fraction", ha="center", va="center")
                #resistanceannotation = ax2.annotate(r"$R = \SI{%.3f}{\kilo\ohm}$" %(data[1][count-1]/1000), xy=(0.5,0.9), xycoords="axes fraction", ha="center", va="center")
                temperatureannotation = ax1.annotate("T = %.3f C" %data[2][count-1], xy=(0.5,0.9), xycoords="axes fraction", ha="center", va="center")
                resistanceannotation = ax2.annotate("R = %.3f kOhm" %(data[1][count-1]/1000), xy=(0.5,0.9), xycoords="axes fraction", ha="center", va="center")
                #try:
                    #averagetemperatureannotation = ax1.annotate(r"$T_{\text{mean}} = \SI{%.3f}{\degreeCelsius}$" %np.nanmean(data[2][plotstart:count]), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #temperaturestandarddeviationannotation = ax1.annotate(r"$\Delta T = \SI{%.3f}{\degreeCelsius}$" %np.nanstd(data[2][plotsart:count]), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                    #averageresistanceannotation = ax2.annotate(r"$R_{\text{mean}} = \SI{%.3f}{\kilo\ohm}$" %(np.nanmean(data[1][plotstart:count])/1000), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #resistancestandarddeviationannotation = ax2.annotate(r"$\Delta R = \SI{%.3f}{\kilo\ohm}$" %(np.nanstd(data[1][plotsart:count])/1000), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                averagetemperatureannotation = ax1.annotate("Tmean = %.3f C" %np.nanmean(data[2][plotstart:count]), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                temperaturestandarddeviationannotation = ax1.annotate("DT = %.3f C" %np.nanstd(data[2][plotstart:count]), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                averageresistanceannotation = ax2.annotate("Rmean = %.3f kOhm" %(np.nanmean(data[1][plotstart:count])/1000), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                resistancestandarddeviationannotation = ax2.annotate("DR = %.3f kOhm" %(np.nanstd(data[1][plotstart:count])/1000), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                #except:
                    #averagetemperatureannotation = ax1.annotate(r"$T_{\text{mean}} = \SI{%.3f}{\degreeCelsius}$" %np.nanmean(data[2][:count]), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #temperaturestandarddeviationannotation = ax1.annotate(r"$\Delta T = \SI{%.3f}{\degreeCelsius}$" %np.nanstd(data[2][:count]), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                    #averageresistanceannotation = ax2.annotate(r"$R_{\text{mean}} = \SI{%.3f}{\kilo\ohm}$" %(np.nanmean(data[1][:count])/1000), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #resistancestandarddeviationannotation = ax2.annotate(r"$\Delta R = \SI{%.3f}{\kilo\ohm}$" %(np.nanstd(data[1][:count])/1000), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                    #averagetemperatureannotation = ax1.annotate("Tmean = %.3f C" %np.nanmean(data[2][:count]), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #temperaturestandarddeviationannotation = ax1.annotate("DT = %.3f C" %np.nanstd(data[2][:count]), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                    #averageresistanceannotation = ax2.annotate("Rmean = %.3f kOhm" %(np.nanmean(data[1][:count])/1000), xy=(0.5,0.85), xycoords="axes fraction", ha="center", va="center")
                    #resistancestandarddeviationannotation = ax2.annotate("DR = %.3f kOhm" %(np.nanstd(data[1][:count])/1000), xy=(0.5,0.8), xycoords="axes fraction", ha="center", va="center")
                plt.draw()
                plt.pause(1)
            
            else:
                break
        except:
            time.sleep(1)
    
    
    print "\n\n + All threads ended!\n"
    
    data = datalist[-1]
    now = datetime.datetime.now()
     
    storagepath = "C:\\Users\\labadmin.MPL\\Documents\\Alex\\Measurements\\Resistance_measurements"
    storagefolder = "/%d-%02d-%02d" %(now.year,now.month,now.day)
    if (os.path.exists(storagepath+storagefolder) == False):
        os.mkdir(storagepath+storagefolder)
    storagepath = storagepath+storagefolder+"/"
     
    if (count != countmax):
        data_copy = np.zeros(shape=(4,count), dtype="float")
        data_copy[0] = np.copy(data[0][:count])
        data_copy[1] = np.copy(data[1][:count])
        data_copy[2] = np.copy(data[2][:count])
        data_copy[3] = np.copy(data[3][:count])
        np.savetxt(storagepath+"Resistance_%d_%02d_%02d_%02d_%02d.txt" % (now.year,now.month,now.day,now.hour,now.minute), np.transpose(data_copy), delimiter=",", newline="\n")        
    else:
        np.savetxt(storagepath+"Resistance_%d_%02d_%02d_%02d_%02d.txt" % (now.year,now.month,now.day,now.hour,now.minute), np.transpose(data), delimiter=",", newline="\n")        
    
    plt.close()
    #plt.rc("text", usetex=True)
    #plt.rc("font", **{"family":"sans-serif","sans-serif":["Helvetica"],"size":11})
    plt.rc("font", **{"size":11})
    #plt.rcParams["text.latex.preamble"]=["\\usepackage{siunitx}","\\usepackage[helvet]{sfmath}","\\sisetup{math-rm=\mathsf,text-rm=\sffamily}"]
    plt.rcParams["legend.fontsize"]=11 
    
    fig = plt.figure(tight_layout=True,figsize=(cm2inch(40),cm2inch(15)))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)
    #ax1.set_xlabel(r"Time $[\SI{}{\second}]$")
    #ax2.set_xlabel(r"Time $[\SI{}{\second}]$")
    #ax1.set_ylabel(r"Temperature $[\SI{}{\degreeCelsius}]$")
    #ax2.set_ylabel(r"Resistance $[\SI{}{\kilo\ohm}]$")
    ax1.set_xlabel("Time [s]")
    ax2.set_xlabel("Time [s]")
    ax1.set_ylabel("Temperature [C]")
    ax2.set_ylabel("Resistance [kOhm]")
    ax2.yaxis.set_major_formatter(FuncFormatter(formatfunc))
    ax1.grid(True,which="both")
    ax2.grid(True,which="both")
    
    ax1.plot(data[0][:count],data[2][:count],linewidth=2,color="red")
    ax2.plot(data[0][:count],data[1][:count],linewidth=2,color="blue")
    ax1.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0])+plotlimit)
    ax1.set_ylim(np.nanmin(data[2][:count])-Tplotlimit,np.nanmax(data[2])+Tplotlimit)
    ax2.set_xlim(np.nanmin(data[0][:count])-plotlimit,np.nanmax(data[0])+plotlimit)
    ax2.set_ylim(np.nanmin(data[1][:count])-Rplotlimit,np.nanmax(data[1])+Rplotlimit)
    
    plt.draw()
    if (raw_input(" + Save plot (y/n) ?: ") == "y"):
        #fig.set_size_inches(cm2inch(13),cm2inch(8.67))
        plt.savefig(storagepath+"Resistance_%d_%02d_%02d_%02d_%02d.pdf" % (now.year,now.month,now.day,now.hour,now.minute), format="pdf")
     
    plt.close()


# -- REMARKS --
# The plotting must be done by the main process.
# The usual raw_input command doesn't work in child processes either. Therefore I implemented a workaround with duplicating the stdin-inputfile.
