#!/usr/bin/env python3
#
# Copyright (c) 2018 Paul Melis
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from sys import stdout
from time import time

class ProgressBar:
    
    def __init__(self, prefix=None, max_value=None, interval=0.5):
        self.max_value = max_value
        self.prefix = ''
        if prefix is not None:
            self.prefix = prefix
        self.interval = interval
        
        self.current_value = 0
        self.last_msg = ''
        self.rotor_index = 0
        self.last_print = time()
        self.t0 = time()
        
    def update(self, value):
        self.current_value = value
        if time() - self.last_print > self.interval:
            self.rotor_index = (self.rotor_index+1) % 4
            rotor = ['-', '\\', '|', '/'][self.rotor_index]
            msg = '{0} {1} {2:,}'.format(self.prefix, rotor, value)
            self._print(msg)
        
    def finish(self):
        self.t1 = time()
        tdiff = self.t1 - self.t0
        msg = '{0} ... {1:,} ({2:.3f}s)'.format(self.prefix, self.current_value, tdiff)
        self._print(msg)
        stdout.write('\n')
        
    def _print(self, msg):
        lm = len(self.last_msg)
        wipe = lm * '\r'
        stdout.write(wipe)
        stdout.write(msg)
        ns = lm - len(msg)
        if ns > 0:
            stdout.write(' '*ns)
        stdout.flush()
        self.last_msg = msg
        self.last_print = time()
    
    
if __name__ == '__main__':
    
    from time import sleep
    b = ProgressBar('Doing something', interval=0.1)
    
    for i in range(300):
        sleep(0.01)
        b.update(300-i)
        
    b.finish()