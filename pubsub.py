#!/usr/bin/python

'''This is the server component of a simple web chat client.'''

import os
import sys
import argparse
import json
from contextlib import contextmanager

import jinja2
from jinja2.loaders import FileSystemLoader
import gevent
from gevent import queue
from gevent import monkey; monkey.patch_all()
import bottle

# You *must* import the green version of zmq or things will
# block and nothing we will work and you will be sad.
from zmq import green as zmq

# This lets us track how many clients are currently connected.
polling = 0

static_dir = os.path.join(
        os.environ.get('OPENSHIFT_REPO_DIR', '.'),
        'static',
        )

template_dir = os.path.join(
        os.environ.get('OPENSHIFT_REPO_DIR', '.'),
        'templates',
        )

# Assume we're deployed in OpenShift if we find
# OPENSHIFT_APP_NAME in the environment.
using_openshift = 'OPENSHIFT_APP_NAME' in os.environ

ctx = zmq.Context()
app = bottle.app()
env = jinja2.Environment(
        loader = FileSystemLoader(template_dir))

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

@contextmanager
def subcontext():
    '''This is a context manager that returns a ZMQ socket connected to the
    internal message bus.  It ensures that the socket is closed when it
    goes out of scope.'''

    subsock = ctx.socket(zmq.SUB)
    subsock.setsockopt(zmq.SUBSCRIBE, '')
    subsock.connect('inproc://pub')

    yield subsock

    subsock.close()

def wait_for_message (rfile):
    '''Wait for a message on the message bus and return it to the
    client.'''

    with subcontext() as subsock:
        # This is like select.poll but understands ZMQ sockets as well as
        # any file-like object with a fileno() method.
        poll = zmq.Poller()
        poll.register(subsock, zmq.POLLIN)
        poll.register(rfile, zmq.POLLIN)

        events = dict(poll.poll())

        # A POLLIN event on rfile indicates that the client
        # has disconnected.
        if rfile.fileno() in events:
            return

        # We only get this far is there's a message available on the bus.
        msg = subsock.recv_json()
        return msg

@app.route('/sub')
def sub():
    '''This is the endpoint for long poll clients.'''

    global polling

    try:
        polling += 1

        # Make sure response will have the correct content type.
        bottle.response.content_type = 'application/json'

        # Allow cross-domain AJAX requests if we're on OpenSfhit
        # (because polls will come in on an alternate port).
        if using_openshift:
            bottle.response.headers['Access-Control-Allow-Origin'] = '*'

        # Because "rfile" is easier to write.
        rfile = bottle.request.environ['wsgi.input'].rfile

        return wait_for_message(rfile)
    finally:
        polling -= 1

@app.route('/<path:path>')
def default(path):
    '''Servers static files from static_dir.'''
    return bottle.static_file(path, static_dir)

@app.route('/')
def index():
    '''Return a default document if no path was specified.'''
    t = env.get_template('index.html')
    return t.render(using_openshift=int(using_openshift))

@app.route('/debug')
def debug():
    '''This lets us see how many /sub requests are active.'''
    bottle.response.content_type = 'text/plain'

    # Using yield because this makes it easier to add
    # additional output.
    yield('polling = %d\n' % polling)

