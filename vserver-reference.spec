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
VROOT=$VROOTDIR/vserver-reference

# Pause vcached
service vcached stop

# Remove old installation first
if [ -d $VROOT ] ; then
    if grep -q $VROOT/proc /proc/mounts ; then
	umount $VROOT/proc
    fi
    if grep -q $VROOT/dev/pts /proc/mounts ; then
	umount $VROOT/dev/pts
    fi
    chattr -R -i $VROOT
    rm -rf $VROOT
fi

$PKGLIBDIR/install-pre.sh vserver-reference

# Mount /dev/pts in reference image
mkdir -p $VROOT/dev/pts
mount -t devpts none $VROOT/dev/pts

# Mount /proc in reference image
mkdir -p $VROOT/proc
mount -t proc none $VROOT/proc

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

# Copy configuration files from host to reference image
for file in /etc/hosts /etc/resolv.conf /etc/yum.conf ; do
    if [ -f $file ] ; then
	echo $file | cpio -p -d -u $VROOT
    fi
done

# Clean up
umount $VROOT/proc
umount $VROOT/dev/pts

$PKGLIBDIR/install-post.sh vserver-reference

# Disable all services in reference image
chroot $VROOT /bin/sh -c "chkconfig --list | awk '{ print \$1 }' | xargs -i chkconfig {} off"

# Restart vcached
service vcached start

%files
%defattr(-,root,root)

%changelog
* Sun Oct 10 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-2.planetlab
- dynamically install reference image

* Tue Sep 14 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-1.planetlab
- initial build
