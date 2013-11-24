#!/usr/bin/python

'''This demonstrates a webapp using Bottle with the "gevent" server.
Unlike the blocking example, this webapp is able to service multiple
simultaneous requests.'''

import os
import sys
import argparse
import time

from gevent import monkey; monkey.patch_all()
import bottle

@bottle.route('/')
def default():
    data = [ 'one', 'two', 'three', 'four' ]
    for d in data:
        yield d
        time.sleep(5)

def main():
    bottle.run(port=9090, server="gevent")

if __name__ == '__main__':
    main()


