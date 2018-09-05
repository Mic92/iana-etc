#!/usr/bin/env python

import hashlib
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime
from typing import IO, Any, Iterator, Set

SERVICES_URL = "https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xml"
SERVICES_XML = "service-names-port-numbers.xml"
SERVICES_FILE = "services"
SERVICES_HEADER = """# See also services(5) and IANA offical page :
# https://www.iana.org/assignments/service-names-port-numbers
#
# (last updated {})
"""

PROTOCOLS_URL = "https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xml"
PROTOCOLS_XML = "protocol-numbers.xml"
PROTOCOLS_FILE = "protocols"
PROTOCOLS_HEADER = """# See also protocols(5) and IANA official page :
# https://www.iana.org/assignments/protocol-numbers
#
# (last updated {})
"""


@contextmanager
def atomic_write(filename: str, mode: str = "w") -> Iterator[IO[Any]]:
    path = os.path.dirname(filename)
    try:
        file = tempfile.NamedTemporaryFile(delete=False, dir=path, mode=mode)
        yield file
        file.flush()
        os.fsync(file.fileno())
        os.rename(file.name, filename)
    finally:
        try:
            os.remove(file.name)
        except OSError as e:
            if e.errno == 2:
                pass
            else:
                raise e


def remove_xml_namespace(doc: ET.Element, namespace: str) -> None:
    ns = f"{namespace}"
    nsl = len(ns)
    for elem in doc.getiterator():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


def compute_sha256(fname: str) -> str:
    hash_sha256 = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def parse_xml(source: str) -> ET.Element:
    tree = ET.parse(source)
    root = tree.getroot()
    remove_xml_namespace(root, "http://www.iana.org/assignments")
    return root


def parse_date(root_xml: ET.Element) -> datetime:
    updated = root_xml.find("updated")
    assert updated is not None and isinstance(updated, str)
    return datetime.strptime(updated, "%Y-%m-%d")


IGNORE_PATTERN = re.compile(
    r".*(unassigned|deprecated|reserved|historic).*", flags=re.IGNORECASE
)


def write_services_file(source: str, destination: str) -> datetime:
    root = parse_xml(source)
    updated = parse_date(root)
    seen: Set[str] = set()
    with atomic_write(destination) as dst:
        dst.write(SERVICES_HEADER.format(updated.strftime("%Y-%m-%d")))
        for r in root.iter("record"):
            desc_ = r.find("description")
            if desc_ is None:
                desc = ""
            else:
                desc = ""

            name_ = r.find("name")
            protocol_ = r.find("protocol")
            number_ = r.find("number")

            if (
                IGNORE_PATTERN.match(desc)
                or name_ is None
                or name_.text is None
                or protocol_ is None
                or protocol_.text is None
                or number_ is None
                or number_.text is None
            ):
                continue
            name = name_.text.lower().replace("_", "-")
            protocol = protocol_.text.lower()
            number = int(number_.text.split("-")[0])

            assignments = "%s/%s" % (number, protocol)
            entry = "%-16s %-10s" % (name, assignments)
            if entry in seen:
                continue
            seen.add(entry)
            dst.write(entry)
            if desc != "" and len(desc) < 70:
                dst.write(" # %s" % desc.replace("\n", ""))
            dst.write("\n")
    return updated


def write_protocols_file(source: str, destination: str) -> datetime:
    root = parse_xml(source)
    updated = parse_date(root)
    with atomic_write(destination) as dst:
        dst.write(PROTOCOLS_HEADER.format(updated.strftime("%Y-%m-%d")))
        for r in root.iter("record"):
            desc_ = r.find("description")
            if desc_ is None or desc_.text is None:
                desc = ""
            else:
                desc = desc_.text
            name_ = r.find("name")
            value_ = r.find("value")
            if (
                IGNORE_PATTERN.match(desc)
                or name_ is None
                or name_.text is None
                or IGNORE_PATTERN.match(name_.text)
                or value_ is None
                or value_.text is None
            ):
                continue
            alias = name_.text.split()[0]
            name = alias.lower()
            value = int(value_.text)
            assignment = "%s %s" % (value, alias)
            dst.write("%-16s %-16s" % (name, assignment))
            if desc != "" and len(desc) < 70:
                dst.write(" # %s" % desc.replace("\n", ""))
            dst.write("\n")
    return updated


def add_entry(tar: tarfile.TarFile, name: str, file: str) -> None:
    def reset(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        tarinfo.mtime = 0
        tarinfo.mode = 0o644
        return tarinfo

    tar.add(file, os.path.join(name, os.path.basename(file)), filter=reset)


def download(url: str, path: str) -> None:
    with atomic_write(path, "wb") as dst, urllib.request.urlopen(url) as src:
        shutil.copyfileobj(src, dst)


def main() -> None:
    if len(sys.argv) < 2:
        print("USAGE: {} download_path".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)
    dest = sys.argv[1]
    os.makedirs(os.path.join(dest, "dist"), exist_ok=True)

    services_xml = os.path.join(dest, SERVICES_XML)
    protocols_xml = os.path.join(dest, PROTOCOLS_XML)
    try:
        download(SERVICES_URL, services_xml)
        download(PROTOCOLS_URL, protocols_xml)
    except OSError as e:
        print(
            "Could not download iana service names and port numbers: {}".format(e),
            file=sys.stderr,
        )
        sys.exit(1)

    services_file = os.path.join(dest, "dist", SERVICES_FILE)
    services_xml_date = write_services_file(services_xml, services_file)

    protocols_file = os.path.join(dest, "dist", PROTOCOLS_FILE)
    protocols_xml_date = write_protocols_file(protocols_xml, protocols_file)

    version = max(services_xml_date, protocols_xml_date).strftime("%Y%m%d")

    name = "iana-etc-%s" % version
    tarball = os.path.join(dest, "dist", name + ".tar.gz")
    with tarfile.open(tarball, "w:gz") as tar:
        add_entry(tar, name, services_xml)
        add_entry(tar, name, services_file)
        add_entry(tar, name, protocols_xml)
        add_entry(tar, name, protocols_file)

    with atomic_write(
        os.path.join(dest, "dist/iana-etc-%s.tar.gz.sha256" % version)
    ) as f:
        f.write(compute_sha256(tarball))

    with atomic_write(os.path.join(dest, ".version")) as f:
        f.write(version)


if __name__ == "__main__":
    main()
