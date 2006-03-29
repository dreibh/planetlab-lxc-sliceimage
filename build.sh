#!/bin/bash
#
# Builds VServer reference image
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2006 The Trustees of Princeton University
#
# $Id: build.sh,v 1.4 2006/03/21 14:57:29 mlhuang Exp $
#

PATH=/sbin:/bin:/usr/sbin:/usr/bin

# In both a normal CVS environment and a PlanetLab RPM
# build environment, all of our dependencies are checked out into
# directories at the same level as us.
if [ -d ../build ] ; then
    PATH=$PATH:../build
    srcdir=..
else
    echo "Error: Could not find sources in either . or .."
    exit 1
fi

export PATH

# Release and architecture to install
releasever=2
basearch=i386

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

# Make /vservers
vroot=$PWD/vservers/vserver-reference
install -d -m 755 $vroot

# Install vserver-reference system
mkfedora -v -r $releasever -a $basearch -g VServer $vroot

# This tells the Boot Manager that it is okay to update
# /etc/resolv.conf and /etc/hosts whenever the network configuration
# changes. Users are free to delete this file.
touch $vroot/etc/AUTO_UPDATE_NET_FILES
