#!/bin/bash
#
# Builds all reference image for vservers.  To optimize for space it
# will only build a complete base vserver reference image and then
# builds "stub" images that are just contain the additional files
# and/or changes for a given reference image.  This is done to shrink
# the RPM itself.  These will be pieced back together with the base
# vserver reference image by an init script that is installed on the
# node.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Marc E. Fiuczynski <mef@cs.princeton.edu>
# Copyright (C) 2004-2007 The Trustees of Princeton University
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

# Do not tolerate errors
set -e

# Path's to the vserver references images and stubs
vrefdir=$PWD/vservers/.vref
vstubdir=$PWD/vservers/.vstub

# XXX: The vserver reference name should be passed in as an argument
# rather than being hardcoded.
vrefname=default

# Make /vservers and default vserver reference image
vref=${vrefdir}/${vrefname}
install -d -m 755 ${vref}

# "Parse" out the packages and groups for mkfedora
vrefpackages=$(grep "^package:.*" vserver-reference.lst | awk '{print $2}')
vrefgroups=$(grep "^group:.*" vserver-reference.lst | awk '{print $2}')
options=""
for package in ${vrefpackages} ; do  options="$options -p $package"; done
for group in ${vrefgroups} ; do options="$options -g $group"; done

# Populate a minimal /dev in the reference image
pl_makedevs ${vref}

# Populate image with vserver-reference packages
pl_setup_chroot ${vref} ${options}

for systemvserver in reference-vservers/*.lst ; do
    NAME=$(basename $systemvserver .lst)

    # "Parse" out the packages and groups for yum
    systempackages=$(grep "^package:.*" $systemvserver | awk '{print $2}')
    systemgroups=$(grep "^group:.*" $systemvserver | awk '{print $2}')

    vdir=${vstubdir}/${NAME}
    rm -rf ${vdir}/*
    install -d -m 755 ${vdir}

    # Clone the base vserver reference to the system vserver reference

       # OPTIMIZATION: Consider using "cp -al" in the future
    (cd ${vref} && find . | cpio -m -d -u -p ${vdir})
    rm -f ${vdir}/var/lib/rpm/__db*

    # Communicate to the initialization script from which vref this stub was cloned
    echo ${vrefname} > ${vdir}.cloned

    # Install the system vserver specific packages
    [ -n "$systempackages" ] && yum -c ${vdir}/etc/yum.conf --installroot=${vdir} -y install $systempackages
    [ -n "$systemgroups" ] && yum -c ${vdir}/etc/yum.conf --installroot=${vdir} -y groupinstall $systemgroups

    # Create a copy of the system vserver w/o the vserver reference files and make it smaller. 
    # This is a three step process:

    # step 1: clean out yum cache to reduce space requirements
    yum -c ${vdir}/etc/yum.conf --installroot=${vdir} -y clean all

    # step 2: figure out the new/changed files in ${vdir} vs. ${vref} and compute ${vdir}.changes
    rsync -anv ${vdir}/ ${vref}/ > ${vdir}.changes
    linecount=$(wc -l ${vdir}.changes | awk ' { print $1 } ')
    let headcount=$linecount-3
    let tailcount=$headcount-1
    head -${headcount} ${vdir}.changes > ${vdir}.changes.1
    tail -${tailcount} ${vdir}.changes.1 > ${vdir}.changes
    rm -f ${vdir}.changes.1

    # step 3: create the ${vdir} with just the list given in ${vdir}.changes 
    install -d -m 755 ${vdir}-tmp/
    rm -rf ${vdir}-tmp/*
    (cd ${vdir} && cpio -m -d -u -p ${vdir}-tmp < ${vdir}.changes)
    rm -rf ${vdir}
    rm -f  ${vdir}.changes
    mv ${vdir}-tmp ${vdir}

done

exit 0
