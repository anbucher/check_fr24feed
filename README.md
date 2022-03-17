# check FR24 Feeder Status
Icinga check command to check status of a Flightradar24 Feeder

Heavily influenced by the great work of the [Monitoring Plugin Collection](https://github.com/Linuxfabrik/monitoring-plugins)

# installation

- copy script to /usr/lib/nagios/plugins/
- make script executable `chmod a+x ./check_fr24feed.py`
- define command in icinga

# help

```
usage: check_fr24feed.py [-h] [-V] [--always-ok] --host HOST_IP [--port HOST_PORT] [-c CRIT] [-w WARN]

This plugin lets you track if a fr24feeder is connected

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  --always-ok           Always returns OK.
  --host HOST_IP        Host IP address of your feeder.
  --port HOST_PORT      Monitor Port of your feeder. Default: 8754
  -c CRIT, --critical CRIT
                        Set the critical threshold seconds since last connection update. Default: 3600
  -w WARN, --warning WARN
                        Set the warning threshold seconds since last connection update. Default: 600
```
# usage example

```
./check_fr24feed.py --host 192.168.1.100
```

# output

```
Feeder: OK - 0s since last status update
Status: connected
```

# Reference
- [Monitoring Plugins Collection](https://github.com/Linuxfabrik/monitoring-plugins)
- [Flightradar24](https://flightradar24.com)
