%define name vserver-reference
%define version 3.0
%define release 1.planetlab%{?date:.%{date}}

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
Requires: util-vserver
AutoReqProv: no
BuildRequires: e2fsprogs, yum

%description
This package creates the virtual server (VServer) reference image used
as the installation base for new PlanetLab slivers.

%define vrootdir /vservers
%define vrefdir %{vrootdir}/%{name}
%define installroot $RPM_BUILD_ROOT%{vrefdir}

%prep
%setup -q

# chattr, mknod, mount, yum all require root privileges. Yech.
if [ $UID -ne 0 ] ; then
    echo You must be root to build the %{name} package.
    false
fi

%build

%install
# Clean up
if grep -q %{installroot}/proc /proc/mounts ; then
    umount %{installroot}/proc
fi
if grep -q %{installroot}/dev/pts /proc/mounts ; then
    umount %{installroot}/dev/pts
fi
chattr -R -i $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_ROOT

# Make /vservers
mkdir -p $RPM_BUILD_ROOT%{vrootdir}
chmod 000 $RPM_BUILD_ROOT%{vrootdir}
chattr +t $RPM_BUILD_ROOT%{vrootdir}

# Make /vservers/vserver-reference
mkdir -p %{installroot}
chattr -t %{installroot}
chmod 755 %{installroot}

MAKEDEV ()
{
    if grep -q %{installroot}/dev/pts /proc/mounts ; then
	umount %{installroot}/dev/pts
    fi
    rm -rf %{installroot}/dev
    mkdir -p %{installroot}/dev
    mknod -m 666 %{installroot}/dev/null c 1 3
    mknod -m 666 %{installroot}/dev/zero c 1 5
    mknod -m 666 %{installroot}/dev/full c 1 7
    mknod -m 644 %{installroot}/dev/random c 1 8
    mknod -m 644 %{installroot}/dev/urandom c 1 9
    mknod -m 666 %{installroot}/dev/tty c 5 0
    mknod -m 666 %{installroot}/dev/ptmx c 5 2
    touch %{installroot}/dev/hdv1
}

# Initialize /dev in reference image
MAKEDEV

# Mount /dev/pts in reference image
mkdir -p %{installroot}/dev/pts
mount -t devpts none %{installroot}/dev/pts

# Mount /proc in reference image
mkdir -p %{installroot}/proc
mount -t proc none %{installroot}/proc

# Create a dummy /etc/fstab in reference image
mkdir -p %{installroot}/etc
cat > %{installroot}/etc/fstab <<EOF
# This fake fstab exists only to please df and linuxconf.
/dev/hdv1	/	ext2	defaults	1 1
EOF

# Prevent all locales from being installed in reference image
mkdir -p %{installroot}/etc/rpm
cat > %{installroot}/etc/rpm/macros <<EOF
%_install_langs en_US:en
EOF

# Initialize RPM database in reference image
mkdir -p %{installroot}/var/lib/rpm
rpm --root %{installroot} --initdb

# XXX Get yum.conf from PlanetLabConf

# Install RPMs in reference image
yum -c ./yum.conf \
%{?sslcertdir:--sslcertdir=%{sslcertdir}} \
--installroot=%{installroot} \
-y groupinstall VServer

# Clean up /dev in reference image
MAKEDEV

# Configure authentication in reference image
chroot %{installroot} authconfig --nostart --kickstart --enablemd5 --enableshadow || :

# Disable all services in reference image
chroot %{installroot} /bin/sh -c "chkconfig --list | awk '{ print \$1 }' | xargs -i chkconfig {} off"

# Clean up
if grep -q %{installroot}/proc /proc/mounts ; then
    umount %{installroot}/proc
fi
if grep -q %{installroot}/dev/pts /proc/mounts ; then
    umount %{installroot}/dev/pts
fi

%clean
# Clean up
if grep -q %{installroot}/proc /proc/mounts ; then
    umount %{installroot}/proc
fi
if grep -q %{installroot}/dev/pts /proc/mounts ; then
    umount %{installroot}/dev/pts
fi
chattr -R -i $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_ROOT

%post
# Copy configuration files from host to reference image
for file in /etc/hosts /etc/resolv.conf /etc/yum.conf ; do
    if [ -f $file ] ; then
	echo $file | cpio -p -d -u %{vrefdir}
    fi
done

%preun

%files
%defattr(-,root,root)
%{vrefdir}

%changelog
* Tue Sep 14 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-1.planetlab
- initial build
