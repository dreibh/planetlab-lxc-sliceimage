%define name vserver-reference
%define version 3.1
%define release 1.planetlab%{?date:.%{date}}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab 3.0
URL: http://cvs.planet-lab.org/cvs/vserver-reference

Summary: VServer reference image
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires: util-vserver, e2fsprogs, yum

AutoReqProv: no
%define debug_package %{nil}

%description
This package creates the virtual server (VServer) reference image used
as the installation base for new PlanetLab slivers.

%prep
%setup -q

%build
RPM_BUILD_DIR=$RPM_BUILD_DIR ./%{name}.init

%install
rm -rf $RPM_BUILD_ROOT
find vservers/vserver-reference | cpio -p -d -u $RPM_BUILD_ROOT/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/vservers/vserver-reference

%post
VROOT=/vservers/vserver-reference

# Make sure the barrier bit is set
setattr --barrier /vservers

# Copy configuration files from host to reference image
for file in /etc/hosts /etc/resolv.conf /etc/yum.conf ; do
    if [ -f $file ] ; then
	echo $file | cpio -p -d -u $VROOT
    fi
done

# Install and parse Management Authority (MA) configuration
if [ -r /etc/planetlab/primary_ma ] ; then
    . /etc/planetlab/primary_ma
    install -D -m 644 /etc/planetlab/primary_ma $VROOT/etc/planetlab/primary_ma
elif [ -d /mnt/cdrom/bootme/cacert ] ; then
    MA_NAME="PlanetLab Central"
    MA_BOOT_SERVER=$(head -1 /mnt/cdrom/bootme/BOOTSERVER)
    MA_BOOT_SERVER_CACERT=/mnt/cdrom/bootme/cacert/$MA_BOOT_SERVER/cacert.pem
    cat > $VROOT/etc/planetlab/primary_ma <<EOF
MA_NAME="$MA_NAME"
MA_BOOT_SERVER="$MA_BOOT_SERVER"
MA_BOOT_SERVER_CACERT="$MA_BOOT_SERVER_CACERT"
EOF
fi

# Install boot server certificate
install -D -m 644 $MA_BOOT_SERVER_CACERT $VROOT/$MA_BOOT_SERVER_CACERT

# Also install in /mnt/cdrom/bootme for backward compatibility
install -D -m 644 $MA_BOOT_SERVER_CACERT $VROOT/mnt/cdrom/bootme/cacert/$MA_BOOT_SERVER/cacert.pem
echo $MA_BOOT_SERVER > $VROOT/mnt/cdrom/bootme/BOOTSERVER

%changelog
* Tue Sep  1 2005 Mark Huang <mlhuang@cs.princeton.edu> 3.1-1.planetlab
- Pre-package vserver-reference instead of building it on nodes

* Tue Nov 30 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-5.planetlab
- PL3118 and PL3131 fix: set barrier bit on /vservers instead of old
  immulink bit. Do not reset the immutable bit on the new
  vserver-reference directory when deleting it after an error.

* Mon Nov 15 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-4.planetlab
- bump release to install Fedora Core 2 updates as of Tue Nov  9 2004
- PL3017 fix: rebuild vserver-reference image in case it was built
  with i386 glibc

* Mon Nov 15 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-4.planetlab
- bump release to install Fedora Core 2 updates as of Tue Nov  9 2004
- PL3017 fix: rebuild vserver-reference image in case it was built
  with i386 glibc

* Sun Oct 10 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-3.planetlab
- dynamically install reference image at init time

* Sun Oct 10 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-2.planetlab
- dynamically install reference image

* Tue Sep 14 2004 Mark Huang <mlhuang@cs.princeton.edu> 3.0-1.planetlab
- initial build
