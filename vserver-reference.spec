%define name vserver
%define version 4.2
%define release 0%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab 4.0
URL: https://svn.planet-lab.org/svn/VserverReference/

Summary: VServer reference image
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires: util-vserver, e2fsprogs, yum
Requires(pre): coreutils

%define debug_package %{nil}

%description
This package does not really exist.

%package reference
Summary: VServer reference image
Group: Applications/System
AutoReqProv: no

%description reference
This package creates the virtual server (VServer) reference image used
as the installation base for new PlanetLab slivers.

%package system-packages
Summary: System slice packages
Group: Applications/System
#Requires: vserver-reference = %{version}-%{release}
Requires: vserver-reference >= 4.2
AutoReqProv: no

%description system-packages
This package installs the RPMS necessary to create system ("root
resource") slices from the virtual server (VServer) reference image.

%prep
%setup -q

%build
pushd VserverReference
./build.sh
popd

%install
rm -rf $RPM_BUILD_ROOT

pushd VserverReference
install -D -m 755 vserver-reference.init $RPM_BUILD_ROOT/%{_initrddir}/vserver-reference
install -D -m 644 vserver-reference.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/vserver-reference
install -D -m 644 vserver-reference.logrotate $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/vserver-reference
find vservers | cpio -p -d -u $RPM_BUILD_ROOT/
popd

%clean
rm -rf $RPM_BUILD_ROOT

# If run under sudo
if [ -n "$SUDO_USER" ] ; then
    # Allow user to delete the build directory
    chown -h -R $SUDO_USER .
    # Some temporary cdroot files like /var/empty/sshd and
    # /usr/bin/sudo get created with non-readable permissions.
    find . -not -perm +0600 -exec chmod u+rw {} \;
    # Allow user to delete the built RPM(s)
    chown -h -R $SUDO_USER %{_rpmdir}/%{_arch}
fi

%files reference
%defattr(-,root,root)
%{_initrddir}/vserver-reference
%{_sysconfdir}/cron.d/vserver-reference
%{_sysconfdir}/logrotate.d/vserver-reference
/vservers/.vref/default

%files system-packages
%defattr(-,root,root)
/vservers/.vstub

%define vcached_pid /var/run/vcached.pid

%pre reference
# Stop vcached
if [ -r %{vcached_pid} ] ; then
    kill $(cat %{vcached_pid})
fi
echo $$ > %{vcached_pid}

# vcached will clean up .vtmp later
mkdir -p /vservers/.vtmp
if [ -d /vservers/.vref ] ; then
    mv /vservers/.vref /vservers/.vtmp/.vref.$RANDOM
fi
if [ -d /vservers/.vcache ] ; then
    mv /vservers/.vcache /vservers/.vtmp/.vcache.$RANDOM
fi

# Allow vcached to run again
rm -f %{vcached_pid}

%post reference
chkconfig --add vserver-reference
chkconfig vserver-reference on
[ "$PL_BOOTCD" = "1" ] || service vserver-reference start

# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/vserver-reference

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
