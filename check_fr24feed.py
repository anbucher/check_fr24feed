#! /usr/bin/env python3
# -*- coding: utf-8; py-indent-offset: 4 -*-
#
# Author:  Andreas Bucher
# Contact: icinga (at) buchermail (dot) de
#          
# License: The Unlicense, see LICENSE file.

# https://github.com/anbucher/check_fr24feed.git

"""Have a look at the check's README for further details.
"""
import argparse
from difflib import diff_bytes
import sys
import json
import datetime
import requests
from requests.structures import CaseInsensitiveDict
from traceback import format_exc

__author__ = 'Andreas Bucher'
__version__ = '2022031701'


DESCRIPTION = """This plugin lets you track if a fr24feeder is connected"""

# Sample URL: https://{feeder_ip}:8754/monitor.json
DEFAULT_PORT = '8754'

DEFAULT_WARN = 600 # seconds
DEFAULT_CRIT = 3600 # seconds


## Define states

# STATE_OK = 0: The plugin was able to check the service and it appeared
# to be functioning properly.

# STATE_WARN = 1: The plugin was able to check the service, but it
# appeared to be above some "warning" threshold or did not appear to be
# working properly.

# STATE_CRIT = 2: The plugin detected that either the service was not
# running or it was above some "critical" threshold.

# STATE_UNKNOWN = 3: Invalid command line arguments were supplied to the
# plugin or low-level failures internal to the plugin (such as unable to
# fork, or open a tcp socket) that prevent it from performing the
# specified operation. Higher-level errors (such as name resolution
# errors, socket timeouts, etc) are outside of the control of plugins and
# should generally NOT be reported as UNKNOWN states.

# Author of state definition
# __author__ = 'Linuxfabrik GmbH, Zurich/Switzerland'
# __version__ = '2020043001'


STATE_OK = 0
STATE_WARN = 1
STATE_CRIT = 2
STATE_UNKNOWN = 3
#STATE_DEPENDENT = 4

########### common functions ###########
# useful functions - Copyright by https://git.linuxfabrik.ch/linuxfabrik/lib/-/blob/master/base3.py

def get_perfdata(label, value, uom, warn, crit, min, max):
    """Returns 'label'=value[UOM];[warn];[crit];[min];[max]
    """
    msg = "'{}'={}".format(label, value)
    if uom is not None:
        msg += uom
    msg += ';'
    if warn is not None:
        msg += str(warn)
    msg += ';'
    if crit is not None:
        msg += str(crit)
    msg += ';'
    if min is not None:
        msg += str(min)
    msg += ';'
    if max is not None:
        msg += str(max)
    msg += ' '
    return msg


def oao(msg, state=STATE_OK, perfdata='', always_ok=False):
    """Over and Out (OaO)

    Print the stripped plugin message. If perfdata is given, attach it
    by `|` and print it stripped. Exit with `state`, or with STATE_OK (0) if
    `always_ok` is set to `True`.
    """
    if perfdata:
        print(msg.strip() + '|' + perfdata.strip())
    else:
        print(msg.strip())
    if always_ok:
        sys.exit(0)
    sys.exit(state)



def coe(result, state=STATE_UNKNOWN):
    """Continue or Exit (CoE)

    This is useful if calling complex library functions in your checks
    `main()` function. Don't use this in functions.

    If a more complex library function, for example `lib.url3.fetch()` fails, it
    returns `(False, 'the reason why I failed')`, otherwise `(True,
    'this is my result'). This forces you to do some error handling.
    To keep things simple, use `result = lib.base3.coe(lib.url.fetch(...))`.
    If `fetch()` fails, your plugin will exit with STATE_UNKNOWN (default) and
    print the original error message. Otherwise your script just goes on.

    The use case in `main()` - without `coe`:

    >>> success, html = lib.url3.fetch(URL)
    >>> if not success:
    >>>     print(html)             # contains the error message here
    >>>>    exit(STATE_UNKNOWN)

    Or simply:

    >>> html = lib.base3.coe(lib.url.fetch(URL))

    Parameters
    ----------
    result : tuple
        The result from a function call.
        result[0] = expects the function return code (True on success)
        result[1] = expects the function result (could be of any type)
    state : int
        If result[0] is False, exit with this state.
        Default: 3 (which is STATE_UNKNOWN)

    Returns
    -------
    any type
        The result of the inner function call (result[1]).
"""

    if result[0]:
        # success
        return result[1]
    print(result[1])
    sys.exit(state)


########### specific check functions ###########

def parse_args():
    """Parse command line arguments using argparse.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s: v{} by {}'.format(__version__, __author__)
    )

    parser.add_argument(
        '--always-ok',
        help='Always returns OK.',
        dest='ALWAYS_OK',
        action='store_true',
        default=False,
    )

    parser.add_argument(
        '--host',
        help='Host IP address of your feeder.',
        dest='HOST_IP',
        required=True,
        default=False,
    )

    parser.add_argument(
        '--port',
        help='Monitor Port of your feeder. Default: %(default)s',
        dest='HOST_PORT',
        default=DEFAULT_PORT,
    )

    parser.add_argument(
        '-c', '--critical',
        help='Set the critical threshold seconds since last connection update. Default: %(default)s',
        dest='CRIT',
        type=int,
        default=DEFAULT_CRIT,
    )

    parser.add_argument(
        '-w', '--warning',
        help='Set the warning threshold  seconds since last connection update. Default: %(default)s',
        dest='WARN',
        type=int,
        default=DEFAULT_WARN,
    )

    return parser.parse_args()


def run_monitor_check(path):
    """Check FR24 feeder.
    """
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"


    # Get data from monitor.json
    try:
        j = requests.get(path, headers=headers)
        json_str = j.json()

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        msg = template.format(type(ex).__name__, ex.args)
        return(False, msg)

    # FAKE request
    # f = open("sample_data/monitor.json")
    # json_str = json.load(f)

    try:
        return (True, json_str)
    except:
        return(False, 'ValueError: No JSON object could be decoded')

def get_sec_last_status(data):
    """Read out seconds since last status update.
    """
    # Get current datetime
    now = datetime.datetime.utcnow()

    # Check date difference
    try:
        ### timeFormat: 2022-03-17 12:39:31
        datetimeunix = int(data['feed_last_ac_sent_time'])
        # lastsentTime = datetime.datetime.strptime(datetimestring, '%Y-%m-%d %H:%M:%S')
        lastsentTime = datetime.datetime.utcfromtimestamp(datetimeunix)
        # calculate time difference
        diffInSecs = (abs(now - lastsentTime ).days * 24 * 60 * 60) + abs(now - lastsentTime ).seconds

        return (True, diffInSecs)
    except:
        return (False, 'ValueError: Last Status could not be parsed') 

def get_metrics(data):

    try:
        metrics = {
            'adsb_tracked': data['feed_num_ac_adsb_tracked'],
            'non_adsb_tracked': data['feed_num_ac_non_adsb_tracked'],
            'sum_tracked': data['feed_num_ac_tracked']
        }

        return (True, metrics)
    except:
        return (False, 'ValueError: Metrics could not be parsed') 

def get_status(data):

    try:
        status = {
            'feed_status': data['feed_status'] ,
            'last_rx_connect_status': data['last_rx_connect_status'],
            'feed_last_connected_time': datetime.datetime.utcfromtimestamp(int(data['feed_last_connected_time'])).strftime("%Y-%m-%d %H:%M:%S")
        }

        return (True, status)
    except:
        return (False, 'ValueError: Status could not be parsed') 



def main():
    """The main function. Hier spielt die Musik.
    """

    # parse the command line, exit with UNKNOWN if it fails
    try:
        args = parse_args()
    except SystemExit:
        sys.exit(STATE_UNKNOWN)

    # init output vars
    msg = ''
    state = STATE_OK
    perfdata = ''

    # Build url
    path = 'http://' + args.HOST_IP + ':' + args.HOST_PORT + '/monitor.json'

    response = coe(run_monitor_check(path))
    diffSecs = coe(get_sec_last_status(response))
    metrics = coe(get_metrics(response))
    status = coe(get_status(response))

    # # Add metrics to perfdata
    perfdata += get_perfdata('adsb_tracked', metrics['adsb_tracked'], None, None, None, 0, None)
    perfdata += get_perfdata('non_adsb_tracked', metrics['non_adsb_tracked'], None, None, None, 0, None)
    perfdata += get_perfdata('sum_tracked', metrics['sum_tracked'], None, None, None, 0, None)


    # check warn and crit thresholds
    try:
        if diffSecs > args.CRIT:
            msg += 'CRIT threshold reached: ' + str(diffSecs)
            state = STATE_CRIT
        else:    
            if diffSecs > args.WARN:
                msg += 'WARN threshold reached: ' + str(diffSecs)
                state = STATE_WARN
            else:
                msg = 'Feeder: OK - ' + str(diffSecs) + 's since last upload'
                msg += '\nStatus: {}'.format(status['feed_status'] + ' since ' + status['feed_last_connected_time']
                )

                state = STATE_OK

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        msg = template.format(type(ex).__name__, ex.args)
        state = STATE_UNKNOWN
        
    oao(msg, state, perfdata)

if __name__ == '__main__':
    try:
        main()
    except Exception:   # pylint: disable=W0703
        """See you (cu)

        Prints a Stacktrace (replacing "<" and ">" to be printable in Web-GUIs), and exits with
        STATE_UNKNOWN.
        """
        print(format_exc().replace("<", "'").replace(">", "'"))
        sys.exit(STATE_UNKNOWN)
