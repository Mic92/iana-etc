# IANA-ETC

Tracks daily changes to IANA’s Assigned Internet Protocol Numbers using Git, and builds `/etc/protocols` and `/etc/services` files via GitHub Actions.

New [releases](https://github.com/Mic92/iana-etc/releases) are created automatically.

## Usage

The script requires Python 3 with no additional dependencies:

```sh
python3 update.py out
```
