#!/usr/bin/python

'''This demonstrates a webapp using the default Bottle server.  When
the webapp is responding to a request, all other requests will block 
until the current response is complete.'''

import os
import sys
import argparse
import time

import bottle

@bottle.route('/')
def default():
    data = [ 'one', 'two', 'three', 'four' ]
    for d in data:
        yield d
        time.sleep(5)

def main():
    bottle.run(port=9090)

if __name__ == '__main__':
    main()


