#!/bin/bash
#
# Builds VServer reference image. Requires the web and boot servers to
# be up, which complicates bootstrap. Alternatively, we could require
# the build server to host a local yum repository. Already, it is
# required to run the same major version of yum as the nodes.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2005 The Trustees of Princeton University
#
# $Id: vserver-reference.init,v 1.17 2005/09/02 19:46:37 mlhuang Exp $
#

# Get the production /etc/yum.conf file. XXX When MAs begin deploying
# their own boot servers and/or code, this will have to change.
curl --silent http://boot.planet-lab.org/$(curl --silent --insecure --form node_id=0 --form file=/etc/yum.conf https://boot.planet-lab.org/db/plnodeconf/getsinglefile.php) > yum.conf

# Solve the bootstrap problem by including any just built packages in
# the yum configuration. This cooperates with the PlanetLab build
# system.
if [ -n "$RPM_BUILD_DIR" ] ; then
    # Remove any [PlanetLab*] sections
    sed -i -f - yum.conf <<EOF
# Match lines between [PlanetLab*] and the next [*
/\[PlanetLab.*\]/I,/^\[/{
# Delete [PlanetLab*]
/\[PlanetLab.*\]/Id
# Done when we see [*
/^\[/b
# Otherwise delete
d
}
EOF

    # And replace them with a section for the RPMS that were just built
    cat >> yum.conf <<EOF
[Bootstrap]
name=Bootstrap RPMS -- $(dirname $RPM_BUILD_DIR)/RPMS/
baseurl=file://$(dirname $RPM_BUILD_DIR)/RPMS/
EOF
fi

# Make /vservers
VROOT=$PWD/vservers/vserver-reference
install -d -m 755 $VROOT

MAKEDEV ()
{
    rm -rf $VROOT/dev
    mkdir -p $VROOT/dev
    mknod -m 666 $VROOT/dev/null c 1 3
    mknod -m 666 $VROOT/dev/zero c 1 5
    mknod -m 666 $VROOT/dev/full c 1 7
    mknod -m 644 $VROOT/dev/random c 1 8
    mknod -m 644 $VROOT/dev/urandom c 1 9
    mknod -m 666 $VROOT/dev/tty c 5 0
    mknod -m 666 $VROOT/dev/ptmx c 5 2
    # For bash command substitution
    ln -nsf ../proc/self/fd /dev/fd
    # For df and linuxconf
    touch $VROOT/dev/hdv1
    # For TUN/TAP
    mkdir -p $VROOT/dev/net
    mknod -m 600 $VROOT/dev/net/tun c 10 200
}

# Initialize /dev in reference image
MAKEDEV

# Mount /dev/pts in reference image
mkdir -p $VROOT/dev/pts
mount -t devpts none $VROOT/dev/pts

# Mount /proc in reference image
mkdir -p $VROOT/proc
mount -t proc none $VROOT/proc

# Clean up before exiting if anything goes wrong
trap "umount $VROOT/proc ; umount $VROOT/dev/pts ; exit 255" ERR

# Create a dummy /etc/fstab in reference image
mkdir -p $VROOT/etc
cat > $VROOT/etc/fstab <<EOF
# This fake fstab exists only to please df and linuxconf.
/dev/hdv1	/	ext2	defaults	1 1
EOF
cp $VROOT/etc/fstab $VROOT/etc/mtab

# Prevent all locales from being installed in reference image
mkdir -p $VROOT/etc/rpm
cat > $VROOT/etc/rpm/macros <<EOF
%_install_langs en_US:en
%_excludedocs 1
%__file_context_path /dev/null
EOF

# This tells the Boot Manager that it is okay to update
# /etc/resolv.conf and /etc/hosts whenever the network configuration
# changes. Users are free to delete this file.
touch $VROOT/etc/AUTO_UPDATE_NET_FILES

# Trick rpm and yum, who read the real root /etc/rpm/macros file
# rather than the one installed in the reference image, despite what
# you might expect the --root and --installroot options to mean. Both
# programs always read $HOME/.rpmmacros.
export HOME=$PWD
ln -sf $VROOT/etc/rpm/macros $PWD/.rpmmacros

# Initialize RPM database in reference image
mkdir -p $VROOT/var/lib/rpm
rpm --root $VROOT --initdb

# Go, baby, go
yum -c yum.conf --installroot=$VROOT -y groupinstall VServer

# Remove stale RPM locks
rm -f $VROOT/var/lib/rpm/__db*

# Clean up /dev in reference image
umount $VROOT/dev/pts
MAKEDEV

# Disable all services in reference image
/usr/sbin/chroot $VROOT /bin/sh -c "/sbin/chkconfig --list | awk '{ print \$1 }' | xargs -i /sbin/chkconfig {} off"

# Clean up
umount $VROOT/proc

exit 0
