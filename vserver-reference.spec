%define name vserver-reference
%define version 3.0
%define release 2.planetlab%{?date:.%{date}}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab 3.0
URL: http://www.planet-lab.org

Summary: VServer reference image
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArchitectures: noarch
Requires: util-vserver, e2fsprogs, yum

%description
This package creates the virtual server (VServer) reference image used
as the installation base for new PlanetLab slivers.

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%post
. /usr/lib/util-vserver/util-vserver-vars

# Make /vservers
mkdir -p $VROOTDIR
chmod 000 $VROOTDIR
chattr +t $VROOTDIR

# Build image in /vservers/.vtmp
mkdir -p $VROOTDIR/.vtmp
VROOT=$(mktemp -d $VROOTDIR/.vtmp/vserver-reference.XXXXXX)

# Make /vservers/.vtmp/vserver-reference.XXXXXX
mkdir -p $VROOT
chattr -t $VROOT
chmod 755 $VROOT

# Clean up before exiting if anything goes wrong
set -e
trap "umount $VROOT/proc ; umount $VROOT/dev/pts ; chattr -R -i $VROOT ; rm -rf $VROOT" EXIT

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
    touch $VROOT/dev/hdv1
}

# Initialize /dev in reference image
MAKEDEV

# Mount /dev/pts in reference image
mkdir -p $VROOT/dev/pts
mount -t devpts none $VROOT/dev/pts

# Mount /proc in reference image
mkdir -p $VROOT/proc
mount -t proc none $VROOT/proc

# Create a dummy /etc/fstab in reference image
mkdir -p $VROOT/etc
cat > $VROOT/etc/fstab <<EOF
# This fake fstab exists only to please df and linuxconf.
/dev/hdv1	/	ext2	defaults	1 1
EOF

# Prevent all locales from being installed in reference image
mkdir -p $VROOT/etc/rpm
cat > $VROOT/etc/rpm/macros <<EOF
%%_install_langs en_US:en
%%_excludedocs 1
%%__file_context_path /dev/null
EOF

# Zap some locks
TMP=`mktemp -d /tmp/%{name}.XXXXXX`
if [ -f /var/lock/rpm/transaction ] ; then
    mv /var/lock/rpm/transaction $TMP
fi
if [ -f /var/run/yum.pid ] ; then
    mv /var/run/yum.pid $TMP
fi

# Initialize RPM database in reference image
mkdir -p $VROOT/var/lib/rpm
rpm --root $VROOT --initdb

# Install RPMs in reference image
yum \
--sslcertdir=/mnt/cdrom/bootme/cacert \
--installroot=$VROOT \
-y groupinstall VServer

# Restore locks
if [ -f $TMP/transaction ] ; then
    mv $TMP/transaction /var/lock/rpm
fi
if [ -f $TMP/yum.pid ] ; then
    mv $TMP/yum.pid /var/run
fi
rmdir $TMP

# Clean up /dev in reference image
umount $VROOT/dev/pts
MAKEDEV

# Disable all services in reference image
chroot $VROOT /bin/sh -c "chkconfig --list | awk '{ print \$1 }' | xargs -i chkconfig {} off"

# Copy configuration files from host to reference image
for file in /etc/hosts /etc/resolv.conf /etc/yum.conf ; do
    if [ -f $file ] ; then
	echo $file | cpio -p -d -u $VROOT
    fi
done

# Clean up
umount $VROOT/proc

# Reset trap
trap - EXIT

# Swap them when complete
mv $VROOT $VROOTDIR
if [ -d $VROOTDIR/vserver-reference ] ; then
    mv $VROOTDIR/vserver-reference $VROOT
    # Let vcached clean it up later
fi
mv $VROOTDIR/$(basename $VROOT) $VROOTDIR/vserver-reference

%postun
. /usr/lib/util-vserver/util-vserver-vars

mkdir -p $VROOTDIR/.vtmp
TMP=$(mktemp -d $VROOTDIR/.vtmp/vserver-reference.XXXXXX)
if [ -d $VROOTDIR/vserver-reference ] ; then
    mv $VROOTDIR/vserver-reference $TMP
    # Let vcached clean it up later
fi

%files
%defattr(-,root,root)

%changelog
* Sun Oct 10 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-2.planetlab
- dynamically install reference image

* Tue Sep 14 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-1.planetlab
- initial build
