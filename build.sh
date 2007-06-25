#!/bin/bash
#
# Builds VServer reference image
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2006 The Trustees of Princeton University
#
# $Id: build.sh,v 1.14 2006/11/13 19:03:53 mlhuang Exp $
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

# Release and architecture to install
releasever=4
basearch=i386

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
)

usage()
{
    echo "Usage: build.sh [OPTION]..."
    echo "	-r release	Fedora release number (default: $releasever)"
    echo "	-a arch		Fedora architecture (default: $basearch)"
    echo "	-h		This message"
    exit 1
}

# Get options
while getopts "r:a:h" opt ; do
    case $opt in
	r)
	    releasever=$OPTARG
	    ;;
	a)
	    basearch=$OPTARG
	    ;;
	h|*)
	    usage
	    ;;
    esac
done

# Do not tolerate errors
set -e

# Make /vservers
vroot=$PWD/vservers/.vref/default
install -d -m 755 $vroot

# Install default reference image
for package in "${packagelist[@]}" ; do
    packages="$packages -p $package"
done
mkfedora -v -r $releasever -a $basearch -k $packages $vroot

# Clean /dev
rm -rf $vroot/dev
mkdir -p $vroot/dev
mknod -m 666 $vroot/dev/null c 1 3
mknod -m 666 $vroot/dev/zero c 1 5
mknod -m 666 $vroot/dev/full c 1 7
mknod -m 644 $vroot/dev/random c 1 8
mknod -m 644 $vroot/dev/urandom c 1 9
mknod -m 666 $vroot/dev/tty c 5 0
mknod -m 666 $vroot/dev/ptmx c 5 2
# For bash command substitution
ln -nsf ../proc/self/fd $vroot/dev/fd
# For df and linuxconf
touch $vroot/dev/hdv1
# For TUN/TAP
mkdir -p $vroot/dev/net
mknod -m 600 $vroot/dev/net/tun c 10 200
# For pseudo ttys
mkdir -p $vroot/dev/pts

# Disable all services in reference image
chroot $vroot sh -c "/sbin/chkconfig --list | awk '{ print \$1 }' | xargs -i /sbin/chkconfig {} off"

# This tells the Boot Manager that it is okay to update
# /etc/resolv.conf and /etc/hosts whenever the network configuration
# changes. Users are free to delete this file.
touch $vroot/etc/AUTO_UPDATE_NET_FILES

exit 0
