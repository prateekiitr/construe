# -*- coding: utf-8 -*-
# pylint: disable-msg=E1101, E0102, E0202
"""
Created on Tue May 05 10:37:17 2015

Small test to try the abductive approach with the dataset from the Mobiguide
project at the BMI lab.

@author: T. Teijeiro
"""

import construe.utils.plotting.plotter as plotter
import construe.acquisition.record_acquisition as IN
import construe.acquisition.obs_buffer as obs_buffer
import construe.acquisition.signal_buffer as sig_buf
import construe.knowledge.observables as o
import construe.knowledge.constants as C
import construe.knowledge.abstraction_patterns as ap
import construe.inference.searching as searching
import construe.inference.reasoning as reasoning
import time
import itertools
import numpy as np
from pprint import pprint as pp
from construe.model import Interval as Iv
from construe.model.interpretation import Interpretation
from construe.utils.units_helper import (msec2samples as ms2sp,
                                            samples2msec as sp2ms,
                                            msec2bpm, bpm2msec)

#ap.include_pwave(False)
#ap.include_twave(False)
ap.set_interpretation_level(2)
#Signal reading
TFACTOR = 50.0
LENGTH = 23040
#Searching settings
KFACTOR = 12
MIN_DELAY = 1750
MAX_DELAY = int(ms2sp(20000)*TFACTOR)
#Overlapping between consecutive fragments
FR_OVERLAP = int(ms2sp(3000))
FR_IDX = 0
INIT = int(FR_IDX * (LENGTH - FR_OVERLAP))
IN.reset()
#Standard annotator used
ANNOTATOR = 'atr'
#Record used
REC = ('/home/tomas/Dropbox/Investigacion/tese/estadias/2015_BMI'
       '/validation/training_dataset/MG008-2015_07_11-ECG-1')
REC = ('/home/local/tomas.teijeiro/Dropbox/Investigacion/tese/validacions/'
       'loose_records/monitoring_160404-1003_SIM')
REC = '/tmp/mit/103'
IN.set_record(REC, ANNOTATOR)
IN.set_offset(INIT)
IN.set_duration(LENGTH)
IN.set_tfactor(TFACTOR)
IN.start()
print('Preloading buffer...')
time.sleep(sp2ms(MIN_DELAY)/(1000.0*TFACTOR))
IN.get_more_evidence()

#Trivial interpretation
interp = Interpretation()
#The focus is initially set in the first observation
interp.focus.append(next(obs_buffer.get_observations()))
########################
### PEKBFS searching ###
########################
print('Starting interpretation')
t0 = time.time()
pekbfs = searching.PEKBFS(interp, KFACTOR)
ltime = (pekbfs.last_time, t0)
while pekbfs.best is None:
    IN.get_more_evidence()
    acq_time = IN.get_acquisition_point()
    #HINT debug code
    fstr = 'Int: {0:05d} '
    for i in xrange(int(sp2ms(acq_time - pekbfs.last_time)/1000.0)):
        fstr += '-'
    fstr += ' Acq: {1}'
    print(fstr.format(int(pekbfs.last_time), acq_time))
    #End of debug code
    filt = ((lambda n : acq_time + n[0][2] >= MIN_DELAY)
                if obs_buffer.get_status() is obs_buffer.Status.ACQUIRING
                                                        else (lambda _ : True))
    pekbfs.step(filt)
    if pekbfs.last_time > ltime[0]:
        ltime = (pekbfs.last_time, time.time())
    if ms2sp((time.time()-ltime[1])*1000.0)*TFACTOR > MAX_DELAY:
        print('Pruning search')
        if pekbfs.open:
            prevopen = pekbfs.open
        pekbfs.prune()
print('Finished in {0:.3f} seconds'.format(time.time()-t0))
print('Created {0} interpretations'.format(interp.counter))
be = pekbfs.best.node
be.recover_old()
brview = plotter.plot_observations(sig_buf.get_signal(
                                         sig_buf.get_available_leads()[0]), be)

#Branches draw
label_fncs = {}
label_fncs['n'] = lambda br: str(br)
label_fncs['e'] = lambda br: ''
brview = plotter.plot_branch(interp, label_funcs=label_fncs, target=be)

#def get_interp_dict(itrp):
#    return {'name':itrp.name, 'children':[get_interp_dict(c) for c in itrp.child]}
#
#d = get_interp_dict(interp)
