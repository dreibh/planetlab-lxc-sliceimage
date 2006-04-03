%define name vserver-reference
%define version 3.1
%define release 3%{?pldistro:.%{pldistro}}%{?date:.%{date}}

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
pushd vserver-reference
./build.sh -r 2
# Not until we can get the build server to run Fedora Core 4 or an
# updated version of yum.
#./build.sh -r 4
popd

%install
rm -rf $RPM_BUILD_ROOT

pushd vserver-reference
install -D -m 755 %{name}.init $RPM_BUILD_ROOT/%{_initrddir}/%{name}
find vservers/vserver-reference | cpio -p -d -u $RPM_BUILD_ROOT/
popd

%clean
rm -rf $RPM_BUILD_ROOT

# If run under sudo
if [ -n "$SUDO_USER" ] ; then
    # Allow user to delete the build directory
    chown -R $SUDO_USER .
    # Some temporary cdroot files like /var/empty/sshd and
    # /usr/bin/sudo get created with non-readable permissions.
    find . -not -perm +0600 -exec chmod u+rw {} \;
    # Allow user to delete the built RPM(s)
    chown -R $SUDO_USER %{_rpmdir}/%{_arch}
fi

%files
%defattr(-,root,root)
%{_initrddir}/%{name}
/vservers/vserver-reference

%define vcached_pid /var/run/vcached.pid

%pre
# Stop vcached
if [ -r %{vcached_pid} ] ; then
    kill $(cat %{vcached_pid})
fi
echo $$ > %{vcached_pid}

# vcached will clean up .vtmp later
mkdir -p /vservers/.vtmp
if [ -d /vservers/vserver-reference ] ; then
    mv /vservers/vserver-reference /vservers/.vtmp/vserver-reference.$RANDOM
fi
if [ -d /vservers/.vcache ] ; then
    mv /vservers/.vcache /vservers/.vtmp/.vcache.$RANDOM
fi

# Allow vcached to run again
rm -f %{vcached_pid}

%post
chkconfig --add %{name}
chkconfig %{name} on
[ "$PL_BOOTCD" = "1" ] || service vserver-reference start

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
