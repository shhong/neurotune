from __future__ import absolute_import
from .tuner import Tuner

class Parameter(object):
    
    def __init__(self, name, units, lbound, ubound, log_scale=False):
        self.name = name
        self.units = units
        self.lbound = lbound
        self.ubound = ubound
        self.log_scale = log_scale
