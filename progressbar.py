#!/usr/bin/env python3
import sys, time

class ProgressBar:
    
    ROTOR = ['-', '\\', '|', '/']

    def __init__(self, prefix=None, max_value=None, interval=0.5):
        self.max_value = max_value
        self.prefix = ''
        if prefix is not None:
            self.prefix = prefix
        self.interval = interval
        
        self.current_value = 0
        self.last_msg = ''
        self.rotor_index = 0
        self.last_print = time.time()
        self.t0 = time.time()
        
    def update(self, value):
        self.current_value = value
        if time.time() - self.last_print > self.interval:
            self.rotor_index = (self.rotor_index+1) % 4
            rotor = self.ROTOR[self.rotor_index]
            msg = '{0} {1} {2:,}'.format(self.prefix, rotor, value)
            self._print(msg)
        
    def finish(self):
        self.t1 = time.time()
        tdiff = self.t1 - self.t0
        msg = '{0} ... {1:,} ({2:.3f}s)'.format(self.prefix, self.current_value, tdiff)
        self._print(msg)
        sys.stdout.write('\n')
        
    def _print(self, msg):
        lm = len(self.last_msg)
        wipe = lm * '\r'
        sys.stdout.write(wipe)
        sys.stdout.write(msg)
        ns = lm - len(msg)
        if ns > 0:
            sys.stdout.write(' '*ns)
        sys.stdout.flush()
        self.last_msg = msg
        self.last_print = time.time()
    
    
if __name__ == '__main__':
    
    b = ProgressBar('Doing something', interval=0.1)
    
    for i in range(300):
        time.sleep(0.01)
        b.update(300-i)
        
    b.finish()