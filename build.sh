#!/bin/bash
#
# Builds VServer reference image
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2006 The Trustees of Princeton University
#
# $Id: build.sh,v 1.20 2007/09/06 20:41:23 faiyaza Exp $
#

PATH=/sbin:/bin:/usr/sbin:/usr/bin

# In both a normal CVS environment and a PlanetLab RPM
# build environment, all of our dependencies are checked out into
# directories at the same level as us.
if [ -d ../build ] ; then
    PATH=$PATH:../build
    srcdir=..
else
    echo "Error: Could not find $(cd .. && pwd -P)/build/"
    exit 1
fi

export PATH

# build.common comes from the build module
. build.common

pl_process_fedora_options $@
shiftcount=$?
shift $shiftcount

# XXX this should be coming from some configuration file
# Packages to install
packagelist=(
bash
coreutils
iputils
kernel-vserver
bzip2
crontabs
diffutils
logrotate
openssh-clients
passwd
rsh
rsync
sudo
tcpdump
telnet
traceroute
time
vixie-cron
wget
which
yum
curl
gzip
perl
python
tar
jre
findutils
)

# vserver-reference packages used for reference image
for package in "${packagelist[@]}" ; do
    packages="$packages -p $package"
done

# Do not tolerate errors
set -e

# Make /vservers
vroot=$PWD/vservers/.vref/default
install -d -m 755 $vroot

# Populate a minimal /dev in the reference image
pl_makedevs $vroot

# Populate image with vserver-reference packages
pl_setup_chroot $vroot $packages

exit 0
