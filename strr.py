"""
****************************************************
 Uniaxial stress-strain plotting and post processing
 can be applied to any of format of data
 Note: The extension to other file formats are 
 worked out. Now MTS files also can be used   
 in addition of Instron files (NIST)

 Uniform format should be made. This has to be the 
 next thing I should work out.(2011 OCT at NIST)   
****************************************************
"""
import os, math, glob
import matplotlib.pyplot as plt
import numpy as np
import scipy.integrate as integrate

print __doc__

"""
iext = 0
iforce = 1
iwid = 2
"""

def __avg__():
    """ Input through raw_input and average the values
    """
    rst = []
    while True:
        val = raw_input('>>>  ')
        if len(val)==0: break
        else: rst.append(float(val))
        pass
    return np.array(rst).mean()

def avgarea():
    """ Call def avg to input thickness and areas' mean values
    """
    while True:
        print 'Input thicknesses'
        t = __avg__()
        print 'Input areas'
        a = __avg__()
        print 'Average areas: ', t * a
        flag = raw_input('type any than blank if you want to exit')
        if len(flag)==0: break
        pass

def param(ifile=False, filename='strr.inp', mode=None):
    """
    Finds and returns certain parameters envolved in analysis
    thickness, Gauge length, upper stress, lower stress,
    binning window size, flag to tell if it is force or stress,
    the corresponding unit either 'kN' or 'N'.  If ifile is False,
    the module takes the values manually. The values can be given
    through 'strr.inp' file.
    
    Thickness, L0(gauge length), W0(transverse width), ifor_str, unit,

    Mode (case insensitive)
      MTS or NIST
      * MTS is the one at GIFT

    Internal variables
      * t        : thickness of the sample
      * L0       : Gauge length
      * W0       : Transverse width of the sample
      * ifor_str : either 'force' or 'stress'
      * unit     : Force unit 'kN' or 'N'
      * delt     : Bin size (binning window size when calculating
             2nd order terms like R-value, strain rate and so on.
      * ls       : Lower stress (default=10 MPa)
      * us       : Upper stress (default=80 MPa)

    If ifile==False:
        Returns t, L0, W0, area, ls, us, delt, ifor_str, unit
    elif ifile==True:
        Returns likewise but from the given file.

    Defaults of the NIST case:
      * ifor_str='force' : ifor_str is either 'force' or 'stress'
      * unit='N'
    Defaults of the MTS case:
      * ifor_str='force'
      # unit='kN'
    """
    if mode==None: raise IOError, 'No mode is given.'

    if mode!=None and type(mode).__name__=='str':
        print '*** %s mode ***'%mode

    if ifile==False:
        ## thickness
        t = raw_input('Thickness of the sample, (default = 0.42) >>')
        ## Gauge length
        L0 = raw_input('Extension Gauge length (default = 50[mm]) >>')
        ## Sample's transverse width
        W0 = raw_input('Transverse width of the sample (default = 12.5) >>')

        # Depending on the controlling software of the system, 
        # it may provide either force or engineering stress
        if mode.upper()=='MTS': ifor_str='force'
        elif mode.upper()=='NIST':  ifor_str='force'
        else: ifor_str = raw_input("Force or stress ('force' or 'stress'>> ")

        ## Force unit should be either 'kN' or 'N'
        if mode.upper()=='MTS':
            unit='kN'; print 'unit [%s]'%unit
        elif mode.upper()=='NIST':
            unit='N'; print 'unit [%s]'%unit
        else: unit = raw_input("Unit of load (N or kN: default is 'kN') >>> ")

        delt = raw_input('Bin size for slope calc (R, SR, HR, default=20) >>')
        print '\nInput Low and up stress from which the slope is calculated'
        ls = raw_input('Lower stress (default=10 MPa)')
        us = raw_input('Upper stress (default=80 MPa)')
        if len(t) == 0: t = 0.42
        else: t = float(t)
        if len(L0) == 0: L0 = 50.
        else: L0 = float(L0)
        if len(W0) == 0: W0 = 12.5
        else: W0 = float(W0)
        if len(ls) == 0: ls = 10.
        else: ls = float(ls)
        if len(us) == 0: us = 80.
        else: us = float(us)
        if len(delt) == 0: delt=20
        else: delt = int(delt)
        if len(unit) == 0: unit ='kN'
        area = t * W0
        print 't, L0, W0, area = ', t, L0, W0, area
        return t, L0, W0, area, ls, us, delt, ifor_str, unit

    elif ifile==True:
        """
        Use saved sample dimensions, ifort_str, and units
        """
        f = open(filename, 'r')
        lines = f.read()
        lines = lines.split('\n')
        myline = lines[1:9]

        tmp = []
        for i in range(8):
            tmp.append(myline[i].split()[0])

        tmp[0] = float(tmp[0])
        tmp[1] = float(tmp[1])
        tmp[2] = float(tmp[2])
        tmp[3] = float(tmp[3])
        tmp[4] = float(tmp[4])
        tmp[5] = int(tmp[5])

        print 't, L0, W0, area = ', tmp[0], tmp[1], tmp[2], tmp[0]*tmp[2]
        f.close()
        ##     t,     L0,    W0,    area,         ls,   ,us,    delt,  ifort_str, unit
        return tmp[0],tmp[1],tmp[2],tmp[0]*tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],    tmp[7]
    else: raise IOError, 'Unexpected case.'
    pass # End of def param

def column(ifile=False, filename='strr.inp'):
    """
    Read column data's format (5 coloums from MTS)
    to find which column corresponds to which physical term.
    * if time is not available, time is estimated back by input
      data acqusition rate under assumption that it is preserved
      to be constant during the entire test.

    Arguments
    =========
      ifile=False
      filename='strr.inp')

    Internal flags
    ==============
      switch : 'y' (Axial value is given as extension [mm])
              'n' (Axial engineering strain [mm/mm])
      itime  : Column # of time [s] (not available when itime=-1)
      iext   : Column # of axial extension
      ifor   : Column # of standard force [kN]
      iwid   : column # of change in width [mm]

    ---> seems to be buggy. It has to be modified. (2011, Oct 11)
    column is now only used for MTS.
    """
    if ifile==False:
        ## whether the axial input is strain or extension
        while True:
            print "Axial Extension[mm] ('y')"
            switch = raw_input("or Axial engineering Strain[mm/mm] ('n') >>")
            if switch == 'y': break
            elif switch =='n': break
            else:
                print "Wrong answer:",
                print " the answer should be either 'y' or 'n'"

        ## data file column order determincation
        print "If time column is not available, type 'n' "
        itime = raw_input('Column # of time [s] (default=0) >>')
        if itime.upper()=='N':
            itime=='-1'
        if switch=='y':
            iext = raw_input('Col # of axial extension[mm] (default = 1) >>')
        else: iext = raw_input('Col # of axial strain[mm/mm] (default = 1) >>')
        ifor = raw_input('Column # of standard force[kN] (default = 3) >>')
        iwid = raw_input('Column # of change in width[mm] (default = 2) >>')

        ## gives the default if a blank string is passed
        if len(itime) == 0: itime = 0
        else:
            if itime!='n': itime = int(itime)
        if len(iext) == 0: iext = 1
        else: iext = int(iext)
        if len(ifor) == 0: ifor = 3
        else: ifor = int(ifor)
        if len(iwid) == 0: iwid = 2
        else: iwid = int(iwid)
        return itime, iext, ifor, iwid, switch

    elif ifile==True: 
        # When input file, "strr.inp", is given.
        f = open(filename, 'r')
        lines = f.readlines()
        lines = lines[9:] # Read from 9th row
        tmp_ = []
        for i in range(5):
            tmp_.append(lines[i].split()[0])
        for i in range(4): #The last one is switch: 'n' or 'y'
            tmp_[i] = int(tmp_[i])
        f.close()
        ## thickness, L0, W2, lower stress, upper stress,
        ## delt, ifor_str, force unit (N or kN)
        #itime, iext, ifor, iwid, switch = column(ifile=ifile)
        return tmp_[0], tmp_[1], tmp_[2], tmp_[3], tmp_[4]
    raise IOError, 'unexpected case'

def delimiter():
    """
    delimiter decl.
    """
    delimt = raw_input("Delimiter separating the data columns(default=',')")
    if len(delimt) == 0:
        delimt =','
    print 'The given delimiter is ', delimt
    return delimt


"""
t = 0.42 # unit: mm
L0 = 50.  # unit: mm
W0 = 12.5 # unit: mm
are
a = t * L0 # unit: mm^2
"""

def pp(mode='MTS', mod=None):
    """
    Post-process the uniaxial tension tests

    Arguments:
    mode = 'MTS'
    mod  = None

    Dependents
    ==========
    glob, param, column, delimiter,
    nist_column_post_process, mts_column_post_process
    """
    import glob
    ## which raw data file and where?
    path = raw_input('Path or Enter(current working directory)  >>')
    extension = raw_input('Extension (e.g. txt or csv .. etc)  >>')


    if mode.upper()=='MTS':
        if len(path)==0: path = os.getcwd()
        else: path = os.getcwd() + os.sep + path
    elif mode.upper()=='NIST':
        if len(path)==0: path = ''
    else: raise IOError, 'unexpected mode.'

    try: extension.split('.')[1]
    except:
        ## files : list of input raw data files
        if len(extension)==0:
            files = glob.glob(
                '%s%s*.TRA'%(path, os.sep)) + glob.glob(
                '%s%s*.TXT'%(path, os.sep)) + glob.glob(
                    '%s%s*.CSV'%(path, os.sep))
        else: files = glob.glob('%s%s*.%s'%(path, os.sep, extension))
    else: files = [extension]
    
    
    if len(files) == 0:
        print '\n*********************************'
        print 'No files in the current directory'
        print 'whose extension is ', extension
        print 'Current directory is ', os.getcwd()
        print '*********************************\n'
    ## 

    ## files to be read ----------------------
    print '\nFiles to be read as below: '
    for i in range(len(files)):
        print files[i]
    for i in range(len(files[-1])/2):
        print '-',
    print '\n'
    ## ---------------------------------------

    if len(files) > 0:
        ## Whether or not to use 'strr.inp'
        iinp = raw_input(" Use 'strr.inp' (y or n)  >> ")
        if iinp == 'y': ifile = True
        else : ifile = False

        # only effetive when ifile is True
        t, L0, W0, area, ls, us, delt, ifor_str, unit = param(
            ifile = ifile,  mode=mode)

        ## column position determination
        ## print the first files of the series
        ## to show how the file is formatted.
        print '\n\n##############################################'
        print 'One of the files is shown to check the columns'
        print '\n\n filename: %s'%files[0]
        with open(files[0]) as myfile:
            for i in range(10):
                print myfile.next(),
        print '##############################################\n\n'
        itime, iext, ifor, iwid, switch = column(ifile=ifile)
        delimt = delimiter()
        ##
        if mode.upper()=='NIST': pass #skip
        elif mode.upper()=='MTS':
            if unit=='kN': coef = 1.
            elif unit=='N': coef = 1e-3
            else:
                print 'be careful when dealing with the unit'
                raw_input('please press the enter')
                coef = 1.
        else:
            # Think twice when you eventually erase this block
            raise IOError

    for i in range(len(files)):
        if mode.upper()=='NIST':
            #-----------------------------------------------#
            # when W0 and t are given,
            # they over-ride the ones in the raw data files.
            nist_column_post_process(
                datafile=files[i],
                #t=t, W0=W0,
                area=area, ls=ls, us=us, delt=delt, 
                delimt=delimt, #ifor_str=ifor_str, unit=unit,
                #path=path, 
                #itime=itime, iext=iext, #ifor=ifor,
                #iwid=iwid, switch=switch, #coef=coef,
                modulus=mod, nhead=3,
                ifig=54, echo=False, lowe=0.05, upe=0.15,
                __figdir__='figs'
                )
            #-----------------------------------------------#
        else:
            #-----------------------------------------------#
            #
            mts_column_post_process(
                datafile=files[i],
                t=t, L0=L0,
                W0=W0, area=area,
                ls=ls, us=us, delt=delt,
                ifor_str=ifor_str, unit=unit,
                path=path, delimt = delimt,
                itime=itime, iext=iext, ifor=ifor,
                iwid=iwid, switch=switch, coef=coef,
                mod=mod
                )
            #-----------------------------------------------#
    pass # end of def pp

def mts_column_post_process(
    datafile=None, t=None, L0=None, W0=None, area=None,
    path=None, itime=None, iext=None, ifor=None, iwid=None,
    switch=None, coef=1., nhead=3,
    mod=None, upe=0.15, lowe=0.05, 
    ifor_str='force', unit='kN',
    __figdir__='figs',
    ls=10, us=80, delt=20,
    delimt=',',
    ):
    """
    The old DATA file's column post process in details.
    Analyze the raw data and writes the physically meaningful
    entities on to '.str' files.
    
    Arguments
    =========
    datafile  : raw data file name
    t         : Initial thickness of the sample
    L0        : Gauge length
    W0        : Width length
    area      : Cross sectional area
    path      : path where the data files are located
    itime     : Column # for time (not available when -1)
    iext      : Column # for axial extension
    ifor      : Column # for axial force
    iwid      : Column # for width
    switch    : axial extension('y') or strain ('n')
    coef      : Coefficient when converting force to stress.
               Refer to the code itself for details.
    nhead     : number of header
    mod       : Modulus. If given, so is enforced the actual modulus.    
    upe       : 0.15 (A single r-value is calculated at this strain)
    lowe      : 0.05 (A single r-value is calculated at this strain, too)
    ifor_str : Force of stress
    unit      : [kN] or [N]    
    __figdir__: 'figs' (figures are saved under this directory)
    ls        : Lower stress  --\
    us        : Uppor stress  ---\--> in which E is linearly interpolated.
    delt      : binning window size (number of elements along an axis)
    delimt    : delimt between columns

    Variables
    =========
    E_l    : logarithmic axial strain
    E_engi : engineering axial strain
    engiw  : Engineering width strain
    wrk    : Plastic work

    Dependents
    ==========
    matplotlib.pyplot as plt, os, scipy.integrate as integrate
    np.concatenate, from lib import __windowed_rate_values__
    from lib import slope, from lib import __uniform_strain_range__

    Returns (the same kinds as nist_column_post_process)
    =======
    FlowStressAtLowE, FlowStressAtUpE, RatLowE, RatUpE, AccRvalueAt15pct,
    InstRMean, InstRSTDV, InstRSlope,
    ys_offset_fromTotalstrain, ys_offset_fromPlasticstrain    
    """
    import matplotlib.pyplot as plt
    import os
    import scipy.integrate as integrate
    from lib import slope
    from lib import __slope__
    from lib import __windowed_rate_values__
    from lib import __uniform_strain_range__

    if None in [t,L0,W0,area,itime,iext,iwid,switch]:
        print '\n\n##############################################'
        with open(datafile) as myfile:
            for i in range(8):
                print myfile.next(),
        print '##############################################\n\n'
    
    if t==None: t=float(raw_input('Thickness [mm]>>'))
    if L0==None: L0=float(raw_input('Gauge length [mm]>>'))
    if W0==None: W0=float(raw_input('Width [mm]>>'))
    if area==None: area=float(t*W0)
    if itime==None: itime=int(raw_input('itime>>'))
    if iext==None: iext=int(raw_input('iext>>'))
    if iwid==None: iwid=int(raw_input('iwid>>'))
    if ifor==None: ifor=int(raw_input('ifor>>'))
    if switch==None: switch=raw_input('axial ext(y) or strain(n)>>')
    if ifor_str==None: switch=raw_input("'force' or 'stress'(n)>>")
    if unit==None: unit=raw_input("'kN' or 'N'")

    if not(os.path.isdir(__figdir__)):
        print'%s does not exist, thus is made now.'%__figdir__
        os.mkdir(__figdir__)

    if ifor_str.upper()!='FORCE' or unit.upper(
        )!='KN' and abs(coef-1.0)<< 0.0001:
        print '\nSuspicious input:'
        print 'ifor_str: %s'%ifor_str
        print 'unit: %s'%unit
        print 'coef: %f'%coef
        raw_input()

    plt.ioff() #plt interactiveness is off

    ## When time is not available, calculates it
    ## by frequency.
    if itime==-1:
        print 'itime is not available'
        print 'The time needs be calculated'
        print 'by the acqusition frequency'
        print 'Type the acqusition frequency'
        acqf = raw_input('[Hz = /time] >>>')
        acqf = float(acqf)

    print 'filename = ', datafile # raw data file name

    f = open(datafile, 'r')
    source = f.read()
    f.close()
    fout = open(
        datafile.split('.')[0] + '.str', 'w' ) # write file

    ## new header ------------------------------------
    fout.writelines('%13s %13s %13s %13s '%(
            'Strain','E_pl','Stress','Plastic_Work'))
    fout.writelines('%13s %13s %13s %13s '%(
            'time','pl_SR','dSig/dEps','R-value'))
    fout.writelines('%13s %13s %13s \n'%(
            'EngiStress','E_pl_trans', 'ER_pl_trans'))
    fout.writelines('%13s %13s %13s %13s '%(
            'NA','NA','MPa','MJ/m^3'))
    fout.writelines('%13s %13s %13s %13s '%(
            's','/s','MPa','NA'))
    fout.writelines('%13s %13s %13s \n'%(
            'NA','NA','NA'))
    ##------------------------------------------------

    lines = source.split('\n')
    header = lines[0] # no way!
    E_l = [] #logarithmic axial strain
    E_engi = [] #engineering axial strain
    E_pl = []
    S = [] #True stress
    engs = []#engineering stress
    E_w = []
    E_t = []
    time = []

    print '\n\n************************************************'
    print 'Width value is given as a traveling value such that '
    print 'it assumes that change of width is positive'
    print '****************************************************\n\n'

    i = 0
    tcc = 0.
    lines = lines[nhead:]
    for j in range(len(lines)):
        try:
            cline = map(float,lines[j].split(delimt))
            cline[iext]
            cline[iwid]
            cline[ifor]
        except ValueError, IndexError: pass
        else:
            ext = cline[iext]
            force = cline[ifor]
            chg_wid = cline[iwid]

            if itime==-1:
                tcc = tcc + 1./acqf
            else: tcc = cline[itime]
            if switch == 'y':  #axial extension [mm]
                el = math.log(ext / L0 + 1)   #true strain
                engie = ext/L0
            elif switch =='n': #axial strain    [mm/mm]
                el = math.log(ext + 1)        #true strain
                engie = ext
            E_l.append(el)
            E_engi.append(engie)

            ## 
            engiw = - chg_wid / W0 #negative width strain
            try: ew = math.log(1.0 + engiw) #convert into true strain
            except: print 'engiw',engiw

            E_w.append(ew)   # logarithmic width strain
            time.append(tcc)

            if ifor_str.upper()=='FORCE':
                if switch =='y':
                    # [kN/mm^2] = 10^3 N/m^s 10^6 = 10&9 N/m^2 = 1000MPa
                    '\sigma = coef * F/A * (e + 1) * 1000'
                    stress = coef * force / area * (ext / L0 + 1) * 1000.
                elif switch =='n':
                    stress = coef * force / area * (ext + 1) * 1000.
                else: raise IOError, "Wrong switch!"
                engi = coef * force /area * 1000.
            elif ifor_str.upper()== 'STRESS':
                if switch.upper() in ['Y','N']:
                    stress = coef * force * (ext / L0 + 1)
                    engi = coef * force
                else : raise IOError, 'Wrong Switch!'
            else: raise IOError

            S.append(stress)
            engs.append(engi)
                #print S[0:10]
            # logarithmic thickness strain
            E_t.append(-(E_l[i]+E_w[i])) #thickness strain is negative
            # try: R_ = E_w[i]/E_t[i] #accumulative r-value
            # except ZeroDivisionError:
            #     R_ = 0.
            # R.append(R_)
            i = i + 1
        pass # end of each lines in the datafile

    if mod==None: mod = slope(x=E_l, y=S, upy=us, lowy=ls)
    else: mod = mod    
    print 'Modulus : ', mod/10**3,' GPa'

    ## plastic strain
    for i in range(len(E_l)):
        E_p = E_l[i] - S[i]/mod
        if E_p < 0:E_pl.append(0)
        else : E_pl.append(E_p)
    ## 

    wrk = integrate.cumtrapz(y=S, x=E_pl) # Plastic work integration
    wrk = np.concatenate(([np.NAN], wrk), axis=0)

    fout_ = open(datafile.split('.')[0]+'.str', 'w')
    ## use __windowed_rate_values__
    R, SR, HR, HRENGI = __windowed_rate_values__(
        fout=fout_, le= E_l, engie = E_engi,
        sig=S, sig_engi=engs, te=E_t, we=E_w,
        time=time, E_pl=E_pl, delt = delt, wrk = wrk)

    ## Illustration of the estimation                          ##
    ## on the uniform deformation trimming.                    ##

    ## Trimming data within the uniform strain range           ##
    ## Input engineering stress instead of force in this case. ##
    maxind = __uniform_strain_range__(force=engs)
    plt.ioff() #interactive off        
    fig = plt.figure()
    fig.clf(); ax=fig.add_subplot(111)
    ax.plot(E_l[::10],    S[::10],      'x',
            label='True Stress', mfc='None')
    ax.plot(E_engi[::10], engs[::10], 'x',
            label='Engineering Stress-strain',   mfc='None')
    ax.plot(E_l[::10],    HR[::10],       'o',
            label=r'$d\sigma/d\varepsilon$',     mfc='None')
    ax.plot(E_engi[::10], HRENGI[::10],   'd',
            label=r'$d\sigma^{engi}/d\epsilon$', mfc='None')
    leg = ax.legend(loc='lower right', fancybox=True)
    leg.get_frame().set_alpha(0.5)
    ax.set_xlim(0.,)
    # maximum point mark with red big circle.
    ax.plot(E_l[maxind], S[maxind], 'o',
            ms=25, mec='red', mfc='None', alpha=0.5,
            markeredgewidth=5)
    ax.plot(E_engi[maxind], engs[maxind],'o',
            ms=25, mec='red', mfc='None', alpha=0.5,
            markeredgewidth=5)
    ax.set_xlabel(r'$\varepsilon$')
    ax.set_ylabel(r'$\sigma$')
    ylimh = (int(max(S) / 100) + 1) * 100
    ax.set_ylim(0., ylimh)
    fig.savefig('%s_sig_hr.pdf'%datafile.split('.csv')[0])
    fig.clf()

    ## array trimming
    E_l    = E_l[:maxind]     #Axial strain
    E_w    = E_w[:maxind]     #Width strain
    E_t    = E_t[:maxind]     #Thickness strain
    R      = R[:maxind]       #Instantaneous R value
    SR     = SR[:maxind]      #Strain rate
    HR     = HR[:maxind]      #Hardening rate
    E_pl   = E_pl[:maxind]    #Plastic strain
    S      = S[:maxind]       #Logarithmic stress
    E_engi  = E_engi[:maxind] #Engineering Stress
    wrk    = wrk[:maxind]     #Plastic work
    time   = time[:maxind]    #time
    ## Trimming data ends -------------------------------------##    

    filename = datafile.split('.')[0]

    #------------------------------------------------------------------
    # typical one value parameter calculation
    # r-values, Yield strength, Ultimate tensile stress

    # R-value lowe~ upe (or best uniform strain) linear interpolation:
    # lower and upper indices: lind & uind
    # 1) lind
    if lowe>max(E_l):
        raise IOError, 'lowe is bigger than max(le)'
    else:
        for i in range(len(E_l)):
            if E_l[i]>lowe:
                lind = i - 1
                break
    # 2) uind
    if max(E_l)<upe:
        print 'max(E_l)< upe'
        print 'index is fixed to be len(E_l)-1'
        raw_input('enter to go on >>')
        uind = len(E_l) - 1
    else:
        for i in range(len(E_l)):
            if E_l[i]>upe:
                uind = i - 1
                break

    # R value 5~15pct (or best uniform strain)
    AccRvalueAt15pct = E_w[uind] / E_t[uind]   #single value
    RVBtwn5_15pct = np.array(R[lind:uind])     #array
    InstRMean = np.array(RVBtwn5_15pct).mean() #Single value
    InstRSTDV = np.array(RVBtwn5_15pct).std()  #Single value

    # RatLowE: R value at the given lowe strain (e.g., 0.05 strain)
    lind0 = lind; lind1 = lind + 1
    x0 = E_l[lind0]; x1 = E_l[lind1]
    y0 = R[lind0];  y1 = R[lind1]
    RatLowE = (y1 - y0) / (x1 - x0) * (lowe - x0) + y0

    # FlowStressAtLowE: logarithmic Flow stress at the given lowe strain
    y0 = S[lind0]; y1 = S[lind1]
    FlowStressAtLowE = (y1 - y0) / (x1 - x0) * (lowe - x0) + y0

    # RatUpE : R value at the given upe strain
    uind0 = uind; uind1 = uind + 1
    x0 = E_l[uind0]; x1 = E_l[uind1]
    y0 = R[uind0]; y1 = R[uind1]
    RatUpE = (y1 - y0) / (x1 - x0) * (upe - x0) + y0

    # FlowStressAtUpE: Flow stress at the given upe strain
    y0 = S[uind0]; y1 = S[uind1]
    FlowStressAtUpE = (y1 - y0) / (x1 - x0) * (upe - x0) + y0

    ## linear slope of the instantaneous r-value
    TimeBtwn5_15pct = np.array(time[lind:uind])
    InstRSlope = __slope__(TimeBtwn5_15pct, RVBtwn5_15pct)

    ## Yield strength finder..
    ## 0.2 pct offset
    for i in range(len(E_l)):
        if E_l[i]>0.002:
            index = i
            break

    # interpolation
    y0 = S[index - 1]; y1 = S[index]
    x0 = E_l[index - 1] ; x1 = E_l[index]
    ys = (y1 - y0) / (x1 - x0) * (0.002 - x0) + y0
    ys_offset_fromTotalstrain = ys

    for i in range(len(E_pl)):
        if E_pl[i]>0.002:
            index = i
            break

    # interpolation
    y0 = S[index-1];  y1 = S[index]
    x0 = E_pl[index-1]; x1 = E_pl[index]
    ys = (y1 - y0) / (x1 - x0) * (0.002 - x0) + y0
    ys_offset_fromPlasticstrain = ys

    ## some more typical figures..
    """
    1) Strain rate vs logarithmic axial strain: str-SR_*.pdf
    2) Hardening rate vs logarithmic axial strain: str-HR_*.pdf
    3) True Stress - plastic strain: str_Epl_*.pdf
    4) R value vp plastic strain + InstRMEan vs plastic strain: str-r_*.pdf
    5) True stress vs total strain: str-e_*.pdf
    6) Total strain vs time: e-time_*.pdf
    """
    #  strain rate
    fig = plt.figure(); fig.clf()
    ax  = fig.add_subplot(111)
    ax.semilogy(E_l, SR, label='strain rate')
    ax.set_xlabel(r'$\varepsilon$', dict(fontsize=20))
    ax.set_ylabel(r'$\dot{\varepsilon^{tot}}$', dict(fontsize=20))
    ax.legend(loc='best')
    fig.savefig('%s%sstr-SR_%s.pdf'%(
            __figdir__, os.sep, datafile.replace('/','_').split('.')[0])
                )
    # hardening rate
    fig = plt.figure(); fig.clf()
    ax  = fig.add_subplot(111)
    ax.semilogy(E_l, HR, label=r'$d\sigma/d\varepsilon^{tot}$')
    ax.set_xlabel(r'$\varepsilon^{tot}$', dict(fontsize=20))
    ax.set_ylabel(r'$d\sigma/d\varepsilon^{tot}$ [MPa]', dict(fontsize=20))
    ax.legend(loc='best')
    fig.savefig('%s%sstr-HR_%s.pdf'%(
            __figdir__, os.sep, datafile.replace('/','_').split('.')[0]))

    ## stress - plastic strain curve
    fig = plt.figure(); fig.clf()
    ax = fig.add_subplot(111)
    ax.plot(E_pl, S, label='Logarithmic stress and plastic strain curve')
    ax.set_xlabel(r'$\varepsilon^{pl}$', dict(fontsize=20))
    ax.set_ylabel(r'$\sigma$ [MPa]', dict(fontsize=20))
    fig.savefig('%s_sigeps.pdf'%filename)
    fig.savefig('%s_sigeps.eps'%filename)
    ax.set_ylim(0., (int(max(S)/100)+1)*100)

    ax.plot(E_l, HR, label=r'Hardening rate')
    ax.set_ylabel(r'$d\sigma/d\varepsilon [MPa]$', dict(fontsize=20))
    ax.set_ylim(0., (int(max(S)/100)+1)*100)
    fig.savefig('%s_HR_sigeps.pdf'%filename)
    fig.savefig('%s_HR_sigeps.eps'%filename)
    fig.clf()

    ## R-value stress
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(E_l, R, label='R-value')
    ax.set_xlabel(r'$\varepsilon$', dict(fontsize=20))
    ax.set_ylabel('R-value', dict(fontsize=20))
    fig.savefig('%s_Reps.pdf'%filename)
    fig.savefig('%s_Reps.eps'%filename)

    fig.clf()

    ## return variables
    return FlowStressAtLowE, FlowStressAtUpE, RatLowE, RatUpE, AccRvalueAt15pct, InstRMean, InstRSTDV, InstRSlope, ys_offset_fromTotalstrain, ys_offset_fromPlasticstrain
# end of def mts_column_post_process






def nist_column_post_process(
    datafile=None, t=None, W0=None, area=None,
    ls=50, us=80, delt=10,# ifor_str, #unit,
    delimt=',',
    #itime, iext, ifor, iwid,
    #switch,
    #coef,
    nhead=3,
    ifig = 54, #default plt figure id
    echo=False, modulus=None, #prescribable modulus [GPa]
    lowe=0.05, upe=0.15, #lower and upper strain for measuring r-value
    __figdir__='figs'
    ):
    """
    NIST file's column post-process in details.
    Calculates strain, stress, R-value(evol), Hardening rate,
    Uniaxial yield stress, R-value at certain strain levels.
    Counter def to this is on MTS.

    Arguments
    =========
      datafile = None
      t        = None
      W0       = None
      area     = None
      ls       = 50
      us       = 80
      delt     = 10
      delimit  = ','
      nhead    = 3
      ifig     = 54
      echo     = False
      modulus  = None
      lowe     = 0.05 (A single r-value is calculated at this strain)
      upe      = 0.15 (A single r-value is calculated at this strain, too)
      __figdir__ = 'figs' (figures are saved under this directory)

    Variables
    =========
      engie             : engineering axial strain
      le                : positive axial strain (total strain)
      we                : negative width strain (total strain)
      te                : negative thickness strain (total strain)
      area (defined as) : Cross sectional area
      sig_engi          : engineering stress
      sig               : true stress
      mod               : Young's modulus
      E_pl              : Plastic strain
      wrk               : Plastic work
      R                 : R-value (defined by le, te and we)
      SR                : Strain rate
      HR                : Hardening rate
      HRENGI            : Engineering hardening rate
      time              : time which is used when calc the strain rate



      sigp              : fitted stress
      hrp               : fitted hardening rate (dsig/deps)
      A                 : The coefficient A
      exponent          : The exponent n
      trim_index        : The resulting trim index from hrp=sig criterion
          * There are several attempts to get trim_index at which maximum
            force is reached. Among others, the method that simply picks
            up the maximum force per se gives the most stable and reliable
            results.

      uind              : Upper index
      lind              : Lower index
      r_15pct_acc       : we[uind] / te[uind]
      R5_15             : R[lind:uind] R-value between 5~15pct or
                         within best uniform strain range
      InstRMean         : np.array(R5_15).mean()
      instRSTDV         : np.array(R5_15).std()
      R_lowe            : Rvalue at lowe(lowe is given as 0.05 as a default)
      R_upe             : Rvalue at upe (upe is given as 0.15 as a default)
      FlowStress_lowe   : Stress at lowe
      FlowStress_upe    : Stress at upe
      t0_15             : time[lind:uind]
      InstRslope        : Instantaneous dot{R-value} array 5~15 range
      ys_offset_fromTotalstrain   : YS at 0.002 offset of tot strain
      ys_offset_fromPlasticstrain : YS    //              pl strain

    Dependents
    ==========
      matplotlib.pyplot as plt, os, numpy as np,
      __nist__triangle_strip__, scipy.integrate as integrate,
      from lib import slope, from lib import __slope__
      from lib import __windowed_rate_values__,
      from lib import __uniform_strain_range__,

    Returns
    =======
      FlowStress_lowe, FlowStress_upe, R_lowe, R_upe,
      r_15pct_acc, InstRMean, InstRSTDV, InstRslope,
      ys_offset_fromTotalstrain, ys_offset_fromPlasticstrain

    Figures
    =======
      1) True stress - plastic strain
          'str_eps_*.pdf, eps'
      2) R value vs plastic strain + InstRMean vs plastic strain
          'str-r_*.pdf, eps'
      3) True stress vs total strain
          'str-e_*.eps'
      4) Total strain vs time
          'e-time_*s.pdf'
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import scipy.integrate as integrate
    import os
    from lib import slope
    from lib import __slope__
    from lib import __windowed_rate_values__
    from lib import __uniform_strain_range__

    if not(os.path.isdir(__figdir__)):
        print'%s does not exist, thus is made now.'%__figdir__
        os.mkdir(__figdir__)

    plt.ioff() #plt interactiveness is off
    path = os.getcwd()

    if echo: print 'filename =%s'%datafile

    f = open(path + os.sep + datafile, 'r')
    header = f.readlines()[:nhead]; f.close()

    tmpa, tmpb = map(float, header[-1].split(','))

    if W0==None: W0 = tmpa
    if t==None: t = tmpb
    if t>W0:
        print 'suspicious dimension found in'
        raise IOError, datafile

    data = np.loadtxt(
        path + os.sep + datafile, skiprows=nhead,
        delimiter=delimt)
    data = data.T

    ### 
    time = data[0] #[s]
    ext = data[1] #[mm]
    force = data[2] #[N]
    l_disp = data[3] #[mm]
    w_disp = data[4] #[mm]

    # adjustment in both l and w displacement
    # following Adam Creuziger -> GL is et to be 1.
    lbar = 24.89  # measured gauge length of axial extensometer
    wbar = 12.725 # measured gauge length of width axtensometer
    ldisp0 = l_disp[0]
    wdisp0 = w_disp[0]

    #-------------------------------------------------------------#
    ## remove the triangle (following Adam Creuziger)
    ## scenario: 1) positive loading 2) unloading and 3) reloading
    initial_index = __nist_triangle_strip__(force)
    ## trimming the variables
    time = time[initial_index:] - time[initial_index] #time-zeroing
    ext = ext[initial_index:]
    force = force[initial_index:]
    l_disp = l_disp[initial_index:]
    w_disp = w_disp[initial_index:]
    ## removal of triangle ends. ---------------------------------#

    # Again, following Adam Creuziger, ---------------------------#
    # the gauge length and the transverse width are finely tuned.
    L0 = ldisp0 + lbar
    W0 = wdisp0 + wbar
    engie = (l_disp - ldisp0) / L0
    engiwe= (w_disp - wdisp0) / W0
    # Width strain should be negative.
    # The value should be multiplied by -1, 
    # since change in width is given.
    engiwe = -1 * engiwe 
    if engiwe[-1]>0.:
        print "width engineering strain is supposed to be minus."
        print "check if everthing is okay."
        raise IOError
    if engie[-1]<0.:
        print "axial engineering strain is suppoed to be positive."
        print "check if everyhing is okay"
        raise IOError
    # ------------------------------------------------------------#

    ## strain ----------------------------------------------------#
    # True Strain e = ln(1 + engie)
    le = np.log(1 + engie)  # positive axial strain
    we = np.log(1 + engiwe) # negative width strain
    te = - (le + we)        # negative thickness strain
    # True Stress s = S * (engie + 1)
    area = W0 * t
    sig_engi = force / area     # N/mm^2 = N/m^2 /10^-6=10^6 Pa=MPa
    sig = sig_engi * (1 + engie)# S = s * (einge + 1) : true stress
    # ------------------------------------------------------------#

    ## modulus (tangent of the slope unless given)
    mod = slope(x=le, y=sig, upy=us, lowy=ls)
    if echo: print '%50s %5.3f [GPa]'%(
        'Tangent Modulus calculated: ', mod / 10**3)
    if modulus!=None and modulus<50*10**3:
        print 'Modulus is supposed to be in [MPa] unit.'
        print 'But the on you typed in is unexpectedly small.'
        if raw_input("To stop type 'n'>>>").upper()=='N':
            raise IOError
    if modulus!=None and echo:
        print '%50s %5.3f [GPa]'%(
            'Tangent Modulus Given ', mod / 10**3)

    ## plastic strain ----------------------------------- #
    E_pl = []
    for i in range(len(le)): #true axial strain
        if modulus!=None: temp = le[i] - sig[i] / modulus
        else: temp = le[i] - sig[i] / mod
        if temp<0: E_pl.append(0.)
        else: E_pl.append(temp)
    E_pl = np.array(E_pl)
    ## -------------------------------------------------- #

    ## plastic work with first element being np.NAN ------ ##
    wrk = integrate.cumtrapz(y=sig, x=E_pl) #work integration
    wrk = np.concatenate(([np.NAN], wrk), axis=0)
    if sig.shape==wrk.shape: pass
    else: raise IOError,'unexpected shape'
    ## ---------------------------------------------------- ##

    ## calculates 2nd order variables by binning the data -------#
    # 1) R-value 2) Strain rate 3) Hardening rate 4) engineering HR
    # through __windowed_rate_values__
    fout = open(
        path + os.sep + datafile.split('.')[0] + '.str',
        'w')
    # R-value, strain rate, hardeing rate, engineering hardening rate
    R, SR, HR, HRENGI = __windowed_rate_values__(
        fout=fout, le=le, engie=engie,
        sig=sig, sig_engi=sig_engi,
        te=te, we=we, time=time,
        E_pl=E_pl, delt=delt, wrk = wrk
        )



    #------------------------------------------------------------------
    # typical one value parameter calculation
    # r-values, Yield strength, Ultimate tensile stress

    # R-value lowe~ upe (or best uniform strain) linear interpolation:
    # lower and upper indices: lind & uind
    # 1) lind
    if lowe>max(le):
        raise IOError, 'lowe is bigger than max(le)'
    else:
        for i in range(len(le)):
            if le[i]>lowe:
                lind = i - 1
                break
    # 2) uind
    if max(le)<upe:
        print 'max(le)< upe'
        print 'index is fixed to be len(le)-1'
        raw_input()
        uind = len(le) - 1
    else:
        for i in range(len(le)):
            if le[i]>upe:
                uind = i - 1
                break

    r_15pct_acc = we[uind] / te[uind]
    if echo: print '%50s %5.3f'%(
        'Accummulated r value upto 15pct:', r_15pct_acc)

    # 5~15 pct (or best uniform strain)
    ## Instantaneous mean R-value
    R5_15 = np.array(R[lind:uind])
    InstRMean = np.array(R5_15).mean()
    InstRSTDV = np.array(R5_15).std()
    if echo: print '%50s %5.3f'%(
        'Mean Instantaneous R-value:', InstRMean)

    # R_lowe: R value at the given lowe strain (e.g., 0.05 strain)
    lind0 = lind; lind1 = lind + 1
    x0 = le[lind0]; x1 = le[lind1]
    y0 = R[lind0];  y1 = R[lind1]
    R_lowe = (y1 - y0) / (x1 - x0) * (lowe - x0) + y0

    # FlowStress_lowe: Flow stress at the given lowe strain
    y0 = sig[lind0]; y1 = sig[lind1]
    FlowStress_lowe = (y1 - y0) / (x1 - x0) * (lowe - x0) + y0

    # R_upe : R value at the given upe strain
    uind0 = uind; uind1 = uind + 1
    x0 = le[uind0]; x1 = le[uind1]
    y0 = R[uind0]; y1 = R[uind1]
    R_upe = (y1 - y0) / (x1 - x0) * (upe - x0) + y0

    # FlowStress_upe: Flow stress at the given upe strain
    y0 = sig[uind0]; y1 = sig[uind1]
    FlowStress_upe = (y1 - y0) / (x1 - x0) * (upe - x0) + y0    

    ## linear slope of the instantaneous r-value
    t0_15 = np.array(time[lind:uind])
    InstRslope = __slope__(t0_15, R5_15)
    if echo:
        print '%50s %5.3e'%(
            'Slope of Instantaneous R-value vs time:',
            InstRslope)

    ## Yield strength finder..
    ## 0.2 pct offset
    for i in range(len(le)):
        if le[i]>0.002:
            index = i
            break

    # interpolatation
    y0 = sig[index - 1]; y1 = sig[index]
    x0 = le[index - 1] ; x1 = le[index]
    ys = (y1 - y0) / (x1 - x0) * (0.002 - x0) + y0
    if echo:
        print '%50s %5.3f [MPa]'%(
            'Total strain 0.2pct offset yield strength:', ys)
    ys_offset_fromTotalstrain = ys

    for i in range(len(E_pl)):
        if E_pl[i]>0.002:
            index = i
            break
        
    # interpolation
    y0 = sig[index-1];  y1 = sig[index]
    x0 = E_pl[index-1]; x1 = E_pl[index]
    ys = (y1 - y0) / (x1 - x0) * (0.002 - x0) + y0
    if echo:
        print '%50s %5.3f [MPa]'%(
            'Plastic strain 0.2pct offset yield strength:', ys)
    ys_offset_fromPlasticstrain = ys
    
    ## Illustration of the estimation
    ## on the uniform deformation trimming.
    
    ## Determination of uniform strain range starts here. #
    maxind = __uniform_strain_range__(force)

    ## Altogether on the same figure
    # 1) Sigma vs. Eps 2) Engineering str-str 3) 
    fig = plt.figure(ifig)
    fig.clf() ; ax=fig.add_subplot(111)
    ax.plot(le[::10],    sig[::10],      'x',
            label='True Stress', mfc='None')
    ax.plot(engie[::10], sig_engi[::10], 'x',
            label='Engineering Stress-strain',   mfc='None')
    ax.plot(le[::10],    HR[::10],       'o',
            label=r'$d\sigma/d\varepsilon$',     mfc='None')
    ax.plot(engie[::10], HRENGI[::10],   'd',
            label=r'$d\sigma^{engi}/d\epsilon$', mfc='None')
    leg = ax.legend(loc='lower right', fancybox=True)
    leg.get_frame().set_alpha(0.5)
    ax.set_xlim(0.,)

    # maximum point mark with red big circle.
    ax.plot(le[maxind], sig[maxind], 'o',
            ms=25, mec='red', mfc='None', alpha=0.5,
            markeredgewidth=5)
    ax.plot(engie[maxind], sig_engi[maxind],'o',
            ms=25, mec='red', mfc='None', alpha=0.5,
            markeredgewidth=5)
    ax.set_xlabel(r'$\varepsilon$')
    ax.set_ylabel(r'$\sigma$')
    ylimh = (int(max(sig) / 100) + 1) * 100    
    ax.set_ylim(0., ylimh)
    fig.savefig('%s_sig_hr.pdf'%datafile.split('.csv')[0])
    fig.clf()
    ### Determination of uniform strain ends here.

    if echo:
        print 'maximum_index', maxind
        print 'estimated uniform strain: %5.2f'%le[maxind]
        pass

    ## trimming all variables have been obtined above.
    le = le[:maxind]             #axial strain
    we = we[:maxind]             #width strain
    te = te[:maxind]             #thickness strain
    R = R[:maxind]               #Instantaneous R value
    SR = SR[:maxind]             #Strain rate
    HR = HR[:maxind]             #Hardening rate
    E_pl = E_pl[:maxind]         #Plastic strain
    sig = sig[:maxind]           #Stress
    sig_engi = sig_engi[:maxind] #Engineering Stress
    wrk = wrk[:maxind]           #Plastic work
    time = time[:maxind]         #Time

    ## some more typical figures...
    """
    1) Strain rate vs logarithmic axial strain: str-SR_*.pdf
    2) Hardening rate vs logarithmic axial strain: str-HR_*.pdf
    3) True Stress - plastic strain: str_Epl_*.pdf
    4) R value vp plastic strain + InstRMEan vs plastic strain: str-r_*.pdf
    5) True stress vs total strain: str-e_*.pdf
    6) Total strain vs time: e-time_*.pdf
    """
    
    #  strain rate
    fig = plt.figure(ifig); fig.clf()
    ax  = fig.add_subplot(111)
    ax.semilogy(le, SR, label='strain rate')
    ax.set_xlabel(r'$\varepsilon$', dict(fontsize=20))
    ax.set_ylabel(r'$\dot{\varepsilon^{tot}}$', dict(fontsize=20))
    ax.legend(loc='best')
    fig.savefig('%s%sstr-SR_%s.pdf'%(
            __figdir__, os.sep, datafile.replace('/','_').split('.')[0])
                )
    # hardening rate
    fig = plt.figure(ifig); fig.clf()
    ax  = fig.add_subplot(111)
    ax.semilogy(le, HR, label=r'$d\sigma/d\varepsilon^{tot}$')
    ax.set_xlabel(r'$\varepsilon^{tot}$', dict(fontsize=20))
    ax.set_ylabel(r'$d\sigma/d\varepsilon^{tot}$ [MPa]', dict(fontsize=20))
    ax.legend(loc='best')
    fig.savefig('%s%sstr-HR_%s.pdf'%(
            __figdir__, os.sep, datafile.replace('/','_').split('.')[0]))



    # Save figures.
    """
    Fig #1 True stress - plastic strain
    'str_Epl_*.pdf, eps'
    """
    R = np.array(R); SR = np.array(SR); HR = np.array(HR)
    fig = plt.figure(ifig)
    fig.clf()
    ax = fig.add_subplot(111)
    ax.plot(E_pl[::10], sig[::10], 'o', mfc='None')
    ax.set_xlabel(r'$\varepsilon^{pl}$', dict(fontsize=20))
    ax.set_ylabel(r'$\sigma$ [MPa]', dict(fontsize=20))
    ax.set_xlim(-0.01,)
    fig.savefig('%s%sstr-epl_%s.pdf'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0]))
    fig.savefig('%s%sstr-epl_%s.eps'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0]))
    """
    Fig #2 R value vs plastic strain + InstRMean vs plastic strain
    'str-r_*.pdf, eps'
    """
    fig = plt.figure(ifig)
    fig.clf()
    ax = fig.add_subplot(111)
    #ax.plot(E_pl[:len(R)], R)
    ax.plot(E_pl[lind:uind], R[lind:uind])
    e0 = E_pl[lind]; e1 = E_pl[uind]
    ax.plot([e0,e1], [InstRMean, InstRMean], '--')
    ax.errorbar((e0 + e1) / 2., InstRMean, yerr=InstRSTDV, fmt='o')
    ax.set_xlabel(r'$\varepsilon^{pl}$', dict(fontsize=20))
    ax.set_ylabel(r'$R^{inst}$', dict(fontsize=20))
    fig.savefig('%s%sstr-r_%s.pdf'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0])
                )
    fig.savefig('%s%sstr-r_%s.eps'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0])
                )
    """
    Fig #3 True stress vs total strain
    'str-e_*.eps'
    """
    fig = plt.figure(ifig)
    fig.clf()
    ax = fig.add_subplot(111)
    ax.plot(le[::10], sig[::10], 'o', mfc='None')
    ax.set_xlabel(r'$\varepsilon^{tot}$', dict(fontsize=20))
    ax.set_ylabel(r'$\sigma$ [MPa]', dict(fontsize=20))
    ax.set_xlim(-0.01,0.01)
    fig.savefig('%s%sstr-e_%s.eps'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0])
                )
    """
    Fig #4 Total strain vs time
    'e-time_*s.pdf'
    """
    fig = plt.figure(ifig)
    fig.clf()
    ax = fig.add_subplot(111)
    ax.plot(time[::10],le[::10], 'o', mfc='None')
    ax.set_xlabel('Time [s]', dict(fontsize=20))
    ax.set_ylabel(r'$\varepsilon^{tot}$', dict(fontsize=20))
    fig.savefig('%s%se-time_%s.pdf'%(
            __figdir__, os.sep,
            datafile.replace('/','_').split('.')[0])
                )

    return FlowStress_lowe, FlowStress_upe, R_lowe, R_upe, r_15pct_acc, InstRMean, InstRSTDV, InstRslope, ys_offset_fromTotalstrain, ys_offset_fromPlasticstrain

def __nist_triangle_strip__(force):
    """
    NIST's triangle loading stripper

    This def removes the triangle (following Adam Creuziger)

     ^ force     /
     |     /\   /
     |  __/  \_/
     |--------------> time
    
    Considering the scenario: 1) positive loading
      2) unloading and 3) reloading

    Dependent:
      numpy as np
    Returns:
      initial_index
    """
    import numpy as np
    ## Scenario: 1) positive loading 2) unloading and 3) reloading

    # 1) find dload/ext < 0
    dforce = np.gradient(force)
    i = 0
    kount = 5 #at least 5 number of data are consistent.
    # 2) dload < 0 
    while True:
        if dforce[i]< 0:
            if all(dforce[i:i+kount]<0): break
                #print 'got the dload<0'
            else: pass
        i = i + 1
    # 3) and  dload > 0 again
    while True:
        if dforce[i]>0:
            if all(dforce[i:i+kount]>0): break
            else: pass
        i = i + 1
    initial_index = i
    return initial_index

class pp_plot:
    def __init__(self, ifig, delt):
        files = glob.glob('*.str')
        for f in files:
            print 'file: %s'%f
            data = np.loadtxt(f, skiprows=2, dtype='str')
            data = data.transpose()
            if len(data)!=11:
                print 'unexpected column length'
                print 'in file%s'%f
            
            eps = map(float,data[0])
            ple = map(float,data[1])
            sig = map(float,data[2])
            wrk = map(float,data[3])
            tim = map(float,data[4])
            psr = data[5]
            hrt = data[6]
            r   = data[7]
            
            try:
                sie = map(float,data[8]) # engineering stress
            except: pass
            
            
            for i in range(len(hrt)):
                try:
                    float(psr[i])
                except:
                    psr[i] = 0; hrt[i] = 0; r[i]=0
                else:
                    psr[i] = float(psr[i]); hrt[i]=float(hrt[i]); r[i]=float(r[i])
        
            figure = plt.figure(ifig)
            ax1 = figure.add_subplot(221);ax2 = figure.add_subplot(222)
            ax3 = figure.add_subplot(223);ax4 = figure.add_subplot(224)
            
            ax0 = plt.figure(ifig+1).add_subplot(111)
            ax5 = plt.figure(ifig+2).add_subplot(111) # hardening rate & flow stress


            temp = ax1.plot(ple, sig)
            color = temp[0].properties()['color']
            ax2.plot(wrk, sig, color=color)
            ax3.plot(ple[delt:], psr[delt:], color=color)
            ax4.plot(ple[delt:], hrt[delt:], color=color)
            ax0.plot(ple[delt:], r[delt:], color=color)
            
            ax5.plot(ple, sig,color=color); ax5.plot(ple[delt:], hrt[delt:],color=color, ls='--')
            r = map(float, r)
            mx = max(r)*1.2
            ax0.set_ylim(0.,mx);
            
            ax1.set_ylim(0.,);ax2.set_ylim(0.,);ax3.set_ylim(0.,)
            ax4.set_ylim(0.,);
            mx = max(sig)*1.2
            ax5.set_ylim(0.,mx);
