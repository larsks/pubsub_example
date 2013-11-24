#!/usr/bin/env python

import os

if 'OPENSHIFT_PYTHON_DIR' in os.environ:
    virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
    virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
    try:
        execfile(virtualenv, dict(__file__=virtualenv))
    except IOError:
        pass

from pubsub import app

if __name__ == '__main__':
    app.run(server='gevent',
            host=os.environ.get('OPENSHIFT_PYTHON_IP', '127.0.0.1'),
            port=os.environ.get('OPENSHIFT_PYTHON_PORT', 8080))

