#
# $Id$
#
%define url $URL$

%define slicefamily %{pldistro}-%{distroname}-%{_arch}

%define name vserver
%define version 4.2
%define taglevel 10

# pldistro already in the rpm name
#%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}
%define release %{taglevel}%{?date:.%{date}}

Summary: VServer reference image for slice family %{slicefamily}
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
# this would not be right
#BuildArch: noarch

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %(echo %{url} | cut -d ' ' -f 2)

%define debug_package %{nil}

%description
This package does not really exist.

%package %{slicefamily}
Summary: VServer reference image
Group: Applications/System
AutoReqProv: no
Requires: util-vserver, e2fsprogs, yum
Requires(pre): util-vserver-core, findutils

%description %{slicefamily}
This package creates the virtual server (VServer) reference image used
as the installation base for new PlanetLab slivers.

%package systemslices-%{slicefamily}
Summary: System slice packages
Group: Applications/System
Requires: vserver-%{slicefamily} >= %{version}-%{release}
AutoReqProv: no

%description systemslices-%{slicefamily} 
This package installs the stubs necessary to create system slices
(typically planetflow) on top of the reference image.

%prep
%setup -q

%build
pushd VserverReference
./build.sh %{pldistro} %{slicefamily}
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

%files %{slicefamily}
%defattr(-,root,root)
%{_initrddir}/vserver-reference
%{_sysconfdir}/cron.d/vserver-reference
%{_sysconfdir}/logrotate.d/vserver-reference
/vservers/.vref/%{slicefamily}

%files systemslices-%{slicefamily}
%defattr(-,root,root)
/vservers/.vstub/%{slicefamily}

%define vcached_pid /var/run/vcached.pid

# XXX: UGLY HACK
%pre %{slicefamily}
test -d /vservers/.vref/%{slicefamily} && \
   find /vservers/.vref/%{slicefamily} -print0 | xargs -0 setattr --~iunlink
:

%post %{slicefamily}
chkconfig --add vserver-reference
chkconfig vserver-reference on
# store the default for nodemanager
[ -f /etc/planetlab/slicefamily ] || { mkdir -p /etc/planetlab ; echo %{slicefamily} > /etc/planetlab/slicefamily ; }
[ "$PL_BOOTCD" = "1" ] || service vserver-reference start

# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/vserver-reference

%changelog
* Thu Jul 03 2008 Daniel Hokka Zakrisson <daniel@hozac.com> - VserverReference-4.2-10
- Use the correct yum.conf to get access to required packages such as pf2slice.

* Mon Jun 30 2008 Daniel Hokka Zakrisson <daniel@hozac.com> - VserverReference-4.2-9
- Scriptlet fix.

* Fri Jun 27 2008 Daniel Hokka Zakrisson <daniel@hozac.com> - VserverReference-4.2-8
- Unset the immutable and iunlink bits to make sure we can install the package.

* Fri Jun 27 2008 Daniel Hokka Zakrisson <daniel@hozac.com> - VserverReference-4.2-7
- Let rpm remove the files.

* Thu Apr 24 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-6
- empty change, this should *not* be a noarch package

* Mon Apr 21 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-5
- tweaked pre script that was removing everything under /vservers/.vref
- dismantle vcached (as far as this module is concerned)
- sudo to log in /var/log/sudo

* Fri Mar 28 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-3 VserverReference-4.2-4
- bugfix, 4.2-3 was broken as the slicefamily stamp could not get created, thus nm issued 'vuseradd -t default'

* Wed Mar 26 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-2 VserverReference-4.2-3
- a single node can now install several instances of this package
- package name contains slicefamily - <pldistro>-<fcdistro>-<arch>
- setattr --iunlink or --~iunlink appropriately (uses /proc/virtual/info)
- does not copy yum.conf from host anymore

* Fri Feb 15 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - vserver-4.2-1 vserver-4.2-2
- vserver image to properly use links rather than copies

* Thu Jan 31 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - vserver-4.2-0 vserver-4.2-1
- more careful scan of the vserver-*.pkgs image specifications

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
