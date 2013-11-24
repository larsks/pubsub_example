#!/usr/bin/python

'''This is the server component of a simple web chat client.'''

import os
import sys
import argparse
import json

import gevent
from gevent import queue
from gevent import monkey; monkey.patch_all()
import bottle

# You *must* import the green version of zmq or things will
# block and nothing we will work and you will be sad.
from zmq import green as zmq

static_dir = os.path.join(
        os.environ.get('OPENSHIFT_REPO_DIR', '.'),
        'static',
        )

ctx = zmq.Context()
app = bottle.app()

pubsock = ctx.socket(zmq.PUB)
pubsock.bind('inproc://pub')

@app.route('/pub', method='POST')
def pub():
    '''The /pub endpoint accepts messages from clients and publishes them to
    pubsock (a ZMQ pub socket).'''
    global pubsock

    pubsock.send_json({
        'message': bottle.request.params.get('message'),
        'nick': bottle.request.params.get('nick'),
        })
    return {'status': 'sent'}

def worker(q, rfile):
    '''A worker is spawned for each long-poll client.  The worker blocks
    while waiting for a message to be received via subsock (a ZMQ sub
    socket) or for a client disconnect.'''

    subsock = ctx.socket(zmq.SUB)
    subsock.setsockopt(zmq.SUBSCRIBE, '')
    subsock.connect('inproc://pub')

    # This is like select.poll but understands ZMQ sockets as well as
    # any file-like object with a fileno() method.
    poll = zmq.Poller()
    poll.register(subsock, zmq.POLLIN)
    poll.register(rfile, zmq.POLLIN)

    while True:
        events = dict(poll.poll())

        # A POLLIN event on rfile indicates that the client
        # has disconnected.
        if rfile.fileno() in events:
            break

        if subsock in events:
            msg = subsock.recv_json()
            q.put(json.dumps(msg))
            break

    subsock.close()
    q.put(StopIteration)

@app.route('/sub')
def sub():
    '''This is the endpoint for long poll clients.  It spawns a
    greenlet to service the request and immediately exits.'''

    q = queue.Queue()
    rfile = bottle.request.environ['wsgi.input'].rfile
    task = gevent.spawn(worker, q, rfile)
    return q

@app.route('/<path:path>')
def default(path):
    '''Servers static files from static_dir.'''
    return bottle.static_file(path, static_dir)

@app.route('/')
def index():
    '''Return a default document if no path was specified.'''
    return bottle.static_file('index.html', static_dir)

