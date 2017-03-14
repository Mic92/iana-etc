# IANA-ETC
[![Build Status](https://travis-ci.org/Mic92/iana-etc.svg?branch=master)](https://travis-ci.org/Mic92/iana-etc)

Tracks changes daily of IANA's Assigned Internet Protocol Numbers using git
and build /etc/protocols and /etc/services files using travis-ci.
New [releases](https://github.com/Mic92/iana-etc/releases) are created automatically.

## USAGE

The script requires python3 without any additional dependencies:

```
$ python3 update.py out
```
