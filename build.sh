#!/bin/bash
#
# Builds all reference image for slices.  To optimize for space it
# will only build a complete base reference image and then
# builds "stub" images that are just contain the additional files
# and/or changes for a given reference image.  This is done to shrink
# the RPM itself.  These will be pieced back together with the base
# image by an init script that is installed on the node.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Marc E. Fiuczynski <mef@cs.princeton.edu>
# Copyright (C) 2004-2007 The Trustees of Princeton University
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

# pldistro expected as $1 
pldistro=$1 ; shift
# this comes from spec's slicefamily
slicefamily=$1; shift

# Do not tolerate errors
set -e

# Path's to the reference images and stubs
# This is inherited from util-vservers
vrefdir=$PWD/vservers/.vref
vref=${vrefdir}/${slicefamily}
# stubs are created in a subdir per slicefamily
vstubdir=$PWD/vservers/.vstub/${slicefamily}

# Create paths
install -d -m 755 ${vref}
install -d -m 755 ${vstubdir}

# Some of the PlanetLab RPMs attempt to (re)start themselves in %post,
# unless the installation is running inside the BootCD environment. We
# would like to pretend that we are.
export PL_BOOTCD=1

# Populate image with sliceimage packages
pl_root_makedevs ${vref}
# locate the packages and groups file
pkgsfile=$(pl_locateDistroFile ../build/ ${pldistro} sliceimage.pkgs)
pl_root_mkfedora ${vref} ${pldistro} $pkgsfile
pl_root_tune_image ${vref}

systemslice_count=$(ls ../build/config.${pldistro}/sliceimage-*.pkgs 2> /dev/null | wc -l)
[ $systemslice_count -gt 0 ] && for systemslice in $(ls ../build/config.${pldistro}/sliceimage-*.pkgs) ; do
    NAME=$(basename $systemslice .pkgs | sed -e s,sliceimage-,,)

    echo "--------START BUILDING system sliceimage ${NAME}: $(date)"

    # "Parse" out the packages and groups for yum
    systempackages=$(pl_getPackages ${pl_DISTRO_NAME} $pldistro $systemslice)
    systemgroups=$(pl_getGroups ${pl_DISTRO_NAME} $pldistro $systemslice)
    systempips=$(pl_getPips ${pl_DISTRO_NAME} $pldistro $systemslice)
    systemgems=$(pl_getGems ${pl_DISTRO_NAME} $pldistro $systemslice)

    vdir=${vstubdir}/${NAME}
    rm -rf ${vdir}/*
    install -d -m 755 ${vdir}

    # Clone the base sliceimage reference to the system sliceimage reference
    (cd ${vref} && find . | cpio -m -d -u -p ${vdir})
    rm -f ${vdir}/var/lib/rpm/__db*

    # Communicate to the initialization script from which vref this stub was cloned
    echo ${slicefamily} > ${vdir}.cloned

    # Install the system sliceimage specific packages
    for yum_package in $systempackages; do
	echo " * yum installing $yum_package"
	yum -c ${vdir}/etc/mkfedora-yum.conf --installroot=${vdir} -y install $yum_package
    done
    for group_plus in $systemgroups; do
	group=$(echo $group_plus | sed -e "s,+++, ,g")
	echo " * yum groupinstalling $group"
        yum -c ${vdir}/etc/mkfedora-yum.conf --installroot=${vdir} -y groupinstall "$group"
    done

    # this requires pip to be available in sliceimage at that point
    # fedora and debian -> python-pip
    # on fedora the command is called pip-python (sigh.)
    for pip in $systempips; do
	echo " * pip installing $pip"
	chroot ${vdir} pip -v install $pip || chroot ${vdir} pip-python -v $pip || echo " * FAILURE with pip $pip"
    done

    # same for gems; comes with ruby in fedora but ruby-devel is most likely a good thing
    # we add --no-rdoc --no-ri to keep it low
    for gem in $systemgems; do
	echo " * gem installing $gem"
	chroot ${vdir} gem install --no-rdoc --no-ri $gem || echo " * FAILURE with gem $gem"
    done

    # search e.g. sliceimage-planetflow.post in config.<pldistro> or in config.planetlab otherwise
    postfile=$(pl_locateDistroFile ../build/ ${pldistro} sliceimage-${NAME}.post || : )

    [ -f $postfile ] && /bin/bash $postfile ${vdir} || :

    # Create a copy of the system sliceimage w/o the sliceimage reference files and make it smaller. 
    # This is a three step process:

    # step 1: clean out yum cache to reduce space requirements
    yum -c ${vdir}/etc/mkfedora-yum.conf --installroot=${vdir} -y clean all

    # step 2: figure out the new/changed files in ${vdir} vs. ${vref} and compute ${vdir}.changes
    rsync -anv ${vdir}/ ${vref}/ > ${vdir}.changes
    linecount=$(wc -l ${vdir}.changes | awk ' { print $1 } ')
    let headcount=$linecount-3
    let tailcount=$headcount-1
    # get rid of the last 3 lines of the rsync output
    head -${headcount} ${vdir}.changes > ${vdir}.changes.1
    # get rid of the first line of the rsync output
    tail -${tailcount} ${vdir}.changes.1 > ${vdir}.changes.2
    # post process rsync output to get rid of symbolic link embellish output
    awk ' { print $1 } ' ${vdir}.changes.2 > ${vdir}.changes
    rm -f ${vdir}.changes.*

    # step 3: create the ${vdir} with just the list given in ${vdir}.changes 
    install -d -m 755 ${vdir}-tmp/
    rm -rf ${vdir}-tmp/*
    (cd ${vdir} && cpio -m -d -u -p ${vdir}-tmp < ${vdir}.changes)
    rm -rf ${vdir}
    rm -f  ${vdir}.changes
    mv ${vdir}-tmp ${vdir}

    # cleanup yum remainings
    rm -rf ${vdir}/build ${vdir}/longbuildroot

    echo "--------DONE BUILDING system sliceimage ${NAME}: $(date)"
done

# search sliceimage.post in config.<pldistro> or in config.planetlab otherwise
postfile=$(pl_locateDistroFile ../build/ ${pldistro} sliceimage.post)

[ -f $postfile ] && /bin/bash $postfile ${vref} || :

# fix sudoers config
[ -f ${vref}/etc/sudoers ] && echo -e "\nDefaults\tlogfile=/var/log/sudo\n" >> ${vref}/etc/sudoers

# cleanup yum remainings
rm -rf ${vref}/build ${vref}/longbuildroot

exit 0
