# import qutip as qp
import numpy as np
import matplotlib.pyplot as plt
# import torch
import scipy 
#from scipy.special import legendre
import time
import math
from scipy.linalg import expm


n_basis=3
basis='legendre'

T=10
dt0=0.5
T0=20
dt1=0.005

point_M=36
point_C=10

a0=-1.0524
a1=-0.0113
a2=0.1809
a3=-0.3979
a4=0.3979

e1=0.3
e2=0.3
J12=0.5

X=np.array([[0,1],[1,0]])
Y=np.array([[0,-1j],[1j,0]])
Z=np.array([[1,0],[0,-1]])
I=np.array([[1,0],[0,1]])

spectral_coeff=np.array([1,1,1,1,1,1])

Hsys=e1/2*(np.kron(I,I)-np.kron(Z,I))+e2/2*(np.kron(I,I)-np.kron(I,Z))+J12*(np.kron(Y,Y)+np.kron(X,X))/4

psi0=np.array([1/np.sqrt(2),1/np.sqrt(2),0,0])

Hs=[np.kron(X,I),np.kron(I,X)]

Hc=a0*np.kron(I,I)+a1*np.kron(Z,Z)+a2*np.kron(X,X)+a3*np.kron(Z,I)+a4*np.kron(I,Z)

def sigmoid(x):
    if x>0:
        return (1-math.exp(-x)) / (1 + math.exp(-x))
    else:
        return (math.exp(x)-1) / (math.exp(x) + 1)
    
def legendre(n,x):
    if n==0:
        return 1
    elif n==1:
        return x
    elif n==2:
        return (3*x**2-1)/2

def u(i,t):
    u=0
    n=n_basis
    for j in range(n):
        if basis == 'legendre':
            u+=spectral_coeff[i*n+j]*legendre(j,2*t/T-1)
    u=sigmoid(u)
    return u

def trotter(t_start,t_end,psi):
        """
        Trotterization of the quantum state under Hamiltonian H(t)
        """
        dt=0.13
        n_step=int(abs(t_end-t_start)/dt)+1
               
        dt=(t_end-t_start)/n_step
        for t in range(n_step):
            H_t=Hsys
            for i in range(len(Hs)):
                H_t=H_t+Hs[i]*u(i,t_start+t*dt)
            dU=expm(-1j*H_t*dt) 
                      
            psi=dU@psi   
        return psi

def computeM():
    m=100
    M=np.zeros((2*n_basis,2*n_basis))
    for i1 in range(2):
        for j1 in range(n_basis):
            for i2 in range(2):
                for j2 in range(n_basis):
                    
                    t1=np.random.uniform(0,T,m)
                    t2=np.random.uniform(0,T,m)
                    z=np.zeros(m)
                    for i in range(m):
                        psi1=trotter(0,t1[i],psi0)
                        psi1=Hs[i1]@psi1
                        psi1=trotter(t1[i],t2[i],psi1)
                        psi1=Hs[i2]@psi1
                        psi1=trotter(t2[i],0,psi1)
                        du1=0.5*(1+u(i1,t1[i]))*(1-u(i1,t1[i]))*legendre(j1,2*t1[i]/T-1)
                        du2=0.5*(1+u(i2,t2[i]))*(1-u(i2,t2[i]))*legendre(j2,2*t2[i]/T-1)
                        z[i]=(du1*du2*np.conjugate(psi0)@psi1).real                       
                    M[i1*n_basis+j1][i2*n_basis+j2]=np.mean(z)*(T**2)
    return M 

def computeMC(n=10):
    
    psi_it=np.zeros((2,n,4),dtype=complex)
    ti=np.linspace(T/(2*n),T*(2*n-1)/(2*n),n)
    for i in range(2):
        for t in range(n):
            psi=trotter(0,ti[t],psi0)
            psi=Hs[i]@psi
            psi=trotter(ti[t],T,psi)
            psi_it[i][t]=psi


    M=np.zeros((2*n_basis,2*n_basis))
    for i1 in range(2):
        for j1 in range(3):
            for i2 in range(2):
                for j2 in range(3):
                    z=np.zeros(n*n)
                    for t1 in range(n):
                        for t2 in range(n):
                            du1=0.5*(1+u(i1,ti[t1]))*(1-u(i1,ti[t1]))*legendre(j1,(2*t1-n+1)/n)
                            du2=0.5*(1+u(i2,ti[t2]))*(1-u(i2,ti[t2]))*legendre(j2,(2*t2-n+1)/n)
                            z[t1*n+t2]=(du1*du2*np.conjugate(psi_it[i1][t1])@psi_it[i2][t2]).real
                    M[i1*n_basis+j1][i2*n_basis+j2]=np.mean(z)*(T**2)

    psi_f=trotter(0,T,psi0)
    C=np.zeros(2*n_basis)
    for i in range(2):
        for j in range(3):
            z=np.zeros(10)
            for t in range(10):
                du=0.5*(1+u(i,ti[t]))*(1-u(i,ti[t]))*legendre(j,(2*t-9)/10)
                z[t]=(du*np.conjugate(psi_f)@Hc@psi_it[i][t]).imag
            C[i*n_basis+j]=-np.mean(z)*T


    return M,C

def directMC():
    def u1(i,t,coeff):
        u=0
        for j in range(3):
            u+=coeff[i*3+j]*legendre(j,2*t/T-1)
        u=sigmoid(u)
        return u
    
    def trotter1(t_start,t_end,psi,coeff):
        n_step=300
               
        dt=(t_end-t_start)/n_step
        for t in range(n_step):
            H_t=Hsys
            for i in range(len(Hs)):
                H_t=H_t+Hs[i]*u1(i,t_start+t*dt,coeff)
            dU=expm(-1j*H_t*dt) 
                      
            psi=dU@psi   
        return psi

    dpsi=np.zeros((6,4),dtype=complex)
    ddv=0.01
    for i in range(2):
        for j in range(3):
            coeffp=spectral_coeff
            coeffp[i*3+j]+=ddv
            psip=trotter1(0,T,psi0,coeffp)
            coeffm=spectral_coeff
            coeffm[i*3+j]-=ddv
            psim=trotter1(0,T,psi0,coeffm)
            dpsi[i*3+j]=(psip-psim)/(2*ddv)

    print(dpsi)
    
    M=np.zeros((2*n_basis,2*n_basis))
    for i in range(6):
        for j in range(6):
            M[i][j]=(np.conjugate(dpsi[i])@dpsi[j]).real

    C=np.zeros(2*n_basis)
    for i in range(6):
        C[i]=-(np.conjugate(dpsi[i])@Hc@psi0).imag

    return M,C
            

def computeC():
    m=10
    C=np.zeros(2*n_basis)
    for i in range(2):
        for j in range(3):
            t=np.random.uniform(0,T,m)
            z=np.zeros(m)
            for k in range(m):
                psi1=trotter(0,t[k],psi0)
                psi1=Hs[i]@psi1
                psi1=trotter(t[k],T,psi1)
                psi1=Hc@psi1
                psi2=trotter(0,T,psi0)
                du=0.5*(1+u(i,t[k]))*(1-u(i,t[k]))*legendre(j,2*t[k]/T-1)
                z[k]=(du*np.conjugate(psi2)@psi1).imag

            C[i*n_basis+j]=-np.mean(z)*T
    return C

def generateH():
    pauli2=[np.kron(I,I),np.kron(I,X),np.kron(I,Y),np.kron(I,Z)
            ,np.kron(X,I),np.kron(X,X),np.kron(X,Y),np.kron(X,Z),
            np.kron(Y,I),np.kron(Y,X),np.kron(Y,Y),np.kron(Y,Z),
            np.kron(Z,I),np.kron(Z,X),np.kron(Z,Y),np.kron(Z,Z)]
    x=np.random.uniform(-1,1,16)
    H=np.zeros((4,4),dtype=complex)
    for i in range(16):
        H+=x[i]*pauli2[i]
    E0=max(np.linalg.eigvals(H))
    H=H/E0
    return H


t=time.localtime()
'''
path='C:\\Users\\insta\\Documents\\coding\\analog_quantum\\analog_virtual_time_evolution\\log\\text\\vte_'+str(t.tm_mday)+str(t.tm_hour)+str(t.tm_min)+'.txt'
file=open(path, 'w')

file.write("time:"+":"+str(t.tm_wday)+":"+str(t.tm_mday)+":"+str(t.tm_hour)+":"+str(t.tm_min)+":"+str(t.tm_sec)+'\n'+'\n')

file.write("settings:"+'\n'+'\n')
file.write("n_basis:"+str(n_basis)+'\n')
file.write("basis:"+str(basis)+'\n')
#file.write("T_trotter:"+str(T)+'\n')
file.write("T_virtual_time_evolution:"+str(T0)+'\n')
file.write("evolution_steps:"+str(dt0)+'\n')
file.write("point_M:"+str(point_M)+'\n')
file.write("point_C:"+str(point_C)+'\n')



psi_i=trotter(0,T,psi0)

file.write('\n'+"initial state:"+str(psi_i)+'\n'+'\n'+'\n'+'\n'+'\n')
'''
dt0=0.7
epoches=120
dE=np.zeros(epoches)
x=np.linspace(0,epoches,epoches)

#Hc=generateH()
E,p=np.linalg.eig(Hc)

E0=np.min(E)
#psi_i=np.array()

for T in [10,15,20,25,30]:
    spectral_coeff=np.array([0.1,0,0,-0.1,0,0])
    for i in range(epoches):
            
        M,C=computeMC()
        spectral_coeff=spectral_coeff+dt0*np.linalg.pinv(M)@C
        psi_p=trotter(0,T,psi0)
        dE[i]=np.log(abs(np.conjugate(psi_p)@Hc@psi_p-E0))/np.log(10)
        print('T='+str(T)+"   epoch="+str(i)+"   lgloss="+str(dE[i]))

    plt.plot(x,dE,label='T='+str(T))

plt.legend()
plt.savefig('log\\figure\\NGD(lr=0.7,H2,100100).png')


#file.close()
    
