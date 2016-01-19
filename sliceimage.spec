%define slicefamily %{pldistro}-%{distroname}-%{_arch}

# historically there was one dummy 'sliceimage' package, and 
# then 2 subpackages with %{slicefamily} and system-%{slicefamily}
# however the python spec2make that we need to use on f>=15 is dumb
# it cannot detect it's an empty/dummy package, and thus includes it
# in e.g. noderepo, which fails
# so we now only have the 2 relevant packages

%define name sliceimage
%define version 5.1
%define taglevel 11

# pldistro already in the rpm name
#%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}
%define release %{taglevel}%{?date:.%{date}}


# we don't really need the standard postinstall process from rpm that
# strips files and byte-compiles python files. all files in this
# package are comming from other rpm files and they've already went
# through this post install processing. - baris
%define __os_install_post %{nil}
%define debug_package %{nil}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %{SCMURL}

# sliceimage per se is just a placeholder
Summary: Slice reference image so node can create slivers of type %{slicefamily}
Name: %{name}-%{slicefamily}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
# in 5.0, this package was named vserver-<>
Obsoletes: vserver-%{slicefamily}
# this would not be right
#BuildArch: noarch
AutoReqProv: no

%description
This package provides the nodes with the root image used as the 
installation base for new slivers of type %{slicefamily}.

%package -n sliceimage-system-%{slicefamily}
Summary: Reference image for system slices
Group: Applications/System
AutoReqProv: no
Requires: sliceimage-%{slicefamily} >= %{version}-%{release}
# in 5.0, this package was named vserver-systemslices-<>
Obsoletes: vserver-systemslices-%{slicefamily}

%description -n sliceimage-system-%{slicefamily} 
This package installs the stubs necessary to create system slices
(typically planetflow) on top of the reference image.

%prep
%setup -q

%build
pushd sliceimage
./build.sh %{pldistro} %{slicefamily}
popd

%install
rm -rf $RPM_BUILD_ROOT

pushd sliceimage
# the path for the root of these is still /vservers/ for compat
find vservers | cpio -p -d -u $RPM_BUILD_ROOT/
popd

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/vservers/.vref/%{slicefamily}

%files -n sliceimage-system-%{slicefamily}
%defattr(-,root,root)
/vservers/.vstub/%{slicefamily}

### for upgrades
%post
if [ "$PL_BOOTCD" = "1" ] ; then
   exit 0
fi
# remove explicit reference to vserver, find out all relevant scripts
initScripts=`find /etc/init.d/ -name '*sliceimage*'`
if [ "$initScripts" != "" ] ; then
   for initscript in $initScripts ; do $initscript start ; done
fi

# need to do this for system slices, for when a new image shows up
# we've already the service installed and enabled, as systemslices requires the plain package
%post -n sliceimage-system-%{slicefamily}
if [ "$PL_BOOTCD" = "1" ] ; then
   exit 0
fi
# remove explicit reference to vserver, find out all relevant scripts
initScripts=`find /etc/init.d/ -name '*sliceimage*'`
if [ "$initScripts" != "" ] ; then
   for initscript in $initScripts ; do $initscript force ; done
fi


#%define vcached_pid /var/run/vcached.pid

%changelog
* Tue Jan 19 2016 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-11
- make cronjob hourly instead of daily

* Wed Feb 18 2015 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-10
- fixed taglevel in specfile

* Tue Jul 22 2014 Thomas Dreibholz <dreibh@simula.no> - sliceimage-5.1-9
- Post-install fix: exit instead of return
- Post-install fix: only call init script when there are init scripts

* Wed Jul 16 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-8
- use systemd unit files to initialize lxc-sliceimage instead of a sysv script

* Mon Apr 28 2014 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-7
- can build pips and gems in sliceimage (currently only gem used in omf)
- requires a recent build/pkgs.py if pkgs file does mention pip or gem

* Wed Jul 03 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-6
- attempt to make lxc-sliceimage (update lxc ref. images) more robust
- in particular by avoiding chroot when simple file operations are involved
- also this activity gets logged into /var/log/lxc-sliceimage.log
- it is still unclear whether stub-based images are correctly updated

* Wed Jun 26 2013 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-5
- fixes for heterogeneous slice/nodes
- addresses PATH and missing eth0 among others

* Fri May 24 2013 Andy Bavier <acb@cs.princeton.edu> - sliceimage-5.1-4
- Fix machine arch in slivers

* Wed Oct 24 2012 Andy Bavier <acb@cs.princeton.edu> - sliceimage-5.1-3
- More flexible <interface> element generation

* Mon Jul 09 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-2
- for linux-containers: populates refs from stubs (for system slices)
- for linux-containers: memory bump to 512M, and add acpi

* Fri Apr 13 2012 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - sliceimage-5.1-1
- first working draft for both mainline and lxc

* Mon Jan 24 2011 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - vserver-reference-5.0-6
- no semantic change - just fixed specfile for git URL

* Wed Dec 29 2010 Daniel Hokka Zakrisson <dhokka@cs.princeton.edu> - vserver-reference-5.0-5
- Remove ugly hack that breaks su/sudo on upgrades.

* Tue Dec 07 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - vserver-reference-5.0-4
- optimize rpm construction - skips stripping and the like

* Mon Jul 05 2010 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - VserverReference-5.0-3
- module name changes

* Fri Mar 12 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-5.0-2
- iron out system slices reference image update

* Fri Jan 29 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-5.0-1
- first working version of 5.0:
- pld.c/, db-config.d/ and nodeconfig/ scripts should now sit in the module they belong to
- nodefamily is 3-fold with pldistro-fcdistro-arch
- new module layout

* Tue Oct 20 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-16
- fix issue about locating the post-install script(s)
- this was causing the onelab distro to miss the /etc/sudoers patch

* Mon Oct 19 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - VserverReference-4.2-15
- - comment out requiretty

* Fri Oct 09 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-14
- can use groups in the pkgs file with +++ for space

* Mon Aug 10 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - VserverReference-4.2-13
- Added remove for all VROOTs rather than the last one.  BUG FIX.

* Tue Mar 24 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-12
- fix for fedora 10

* Thu Oct 02 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - VserverReference-4.2-11
- on 64bits archs, locates util-vserver's config file correctly

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

%define module_current_branch 4.2
