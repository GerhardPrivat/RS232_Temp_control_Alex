import numpy as np
import matplotlib.pyplot as plt
import math

from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator
from scipy.optimize import curve_fit

def f(x,a,b,c):
    return (a+b*np.log(x)+c*np.log(x))**(-1)

def f_inv(y,a,b,c):
    Y = (a-(1/y))/(2*c)
    X = ((b/(3*c))**3+Y**2)**(1/2)
    return math.exp( (X-Y)**(1/3) - (X+Y)**(1/3) )

def cm2inch(x):
    return x/2.54

def formatfunc(x, pos):
    return "%.2f" %(x/1e3)

settemp = raw_input("Set temperature (C): ")
settemp = round(float(settemp))
print settemp

referencesetpoint = settemp-settemp%5#round(settemp/10)*10
T1 = referencesetpoint-5
T2 = referencesetpoint+5

parameters = np.loadtxt("Thermistorparameters.txt", delimiter=",", dtype="float")
parameters = parameters.T

for ite in range(len(parameters[0])):
	if (parameters[0][ite] == T1):
		A1 = T1 #"%07.3f" % T1
		A2 = parameters[1][ite]*100e3 #"%07.3f" % (parameters[1][ite]*100e3)
	elif (parameters[0][ite] == referencesetpoint):
		B1 = referencesetpoint #"%07.3f" % referencesetpoint
		B2 = parameters[1][ite]*100e3# "%07.3f" % (parameters[1][ite]*100e3)
	elif (parameters[0][ite] == T2):
		C1 = T2 #"%07.3f" % T2
		C2 = parameters[1][ite]*100e3 #"%07.3f" % (parameters[1][ite]*100e3)

print "A1: ",A1
print "A2: ",A2
print "B1: ",B1
print "B2: ",B2
print "C1: ",C1
print "C2: ",C2

T = np.array([A1,B1,C1])
R = np.array([A2,B2,C2])

R_array = np.linspace(1600,200e3,100e3)

popt,pcov = curve_fit(f,R,T)
a = popt[0]
b = popt[1]
c = popt[2]


#plt.rc("text", usetex=True)
#plt.rc("font", **{"family":"sans-serif","sans-serif":["Helvetica"],"size":11})
plt.rc("font", **{"size":11})
#plt.rcParams["text.latex.preamble"]=["\\usepackage{siunitx}","\\usepackage[helvet]{sfmath}","\\sisetup{math-rm=\mathsf,text-rm=\sffamily}"]
plt.rcParams["legend.fontsize"]=11

plt.ion()
fig = plt.figure(tight_layout=True,figsize=(cm2inch(40),cm2inch(15)))
ax1 = fig.add_subplot(1,2,2)
ax2 = fig.add_subplot(1,2,1)

ax1.grid(True)
ax1.plot(A2,A1,marker="x",markersize=8,markeredgewidth=2,color="red")
ax1.plot(B2,B1,marker="x",markersize=8,markeredgewidth=2,color="lime")
ax1.plot(C2,C1,marker="x",markersize=8,markeredgewidth=2,color="darkorange")
ax1.plot(R_array,f(R_array,a,b,c),linewidth=2,color="blue")
#ax1.set_xlabel(r"Resistance $[\SI{}{\kilo\ohm}]$")
#ax1.set_ylabel(r"Temperature $[\SI{}{\degreeCelsius}]$")
ax1.set_xlabel("Resistance [kOhm]")
ax1.set_ylabel("Temperature [C]")
ax1.set_ylim(15,160)
ax1.xaxis.set_major_formatter(FuncFormatter(formatfunc))

ax2.grid(True,which="both")
ax2.plot(A2,A1,marker="x",markersize=8,markeredgewidth=2,color="red")
ax2.plot(B2,B1,marker="x",markersize=8,markeredgewidth=2,color="lime")
ax2.plot(C2,C1,marker="x",markersize=8,markeredgewidth=2,color="darkorange")
ax2.plot(R_array,f(R_array,a,b,c),linewidth=2,color="blue")
ax2.set_xlabel("Resistance [kOhm]")
ax2.set_ylabel("Temperature [C]")
ax2.set_ylim(A1-10,C1+10)
ax2.set_xlim(C2-2e3,A2+2e3)
ax2.xaxis.set_major_formatter(FuncFormatter(formatfunc))
ax2.xaxis.set_minor_locator(MultipleLocator(500))

checkout = raw_input(" + Save plot (y/n)?: ")
if (checkout == "y"):
    plt.savefig("Steinhart-Hart-Equation-Fit-Plot.pdf", format="pdf")
    np.savetxt("Steinhart-Hart-Equation_Fit_Paramters.txt",np.asarray([a,b,c]))
    plt.close()

