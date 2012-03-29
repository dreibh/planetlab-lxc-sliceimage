%define name vserver-sliceimage
%define version 5.1
%define taglevel 0

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %{SCMURL}

Summary: vserver-specific node code for slice families
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires: util-vserver, e2fsprogs, yum
BuildArch: noarch

%description
vserver-specific initscript for handling slice images
initializes vrefs from stubs for system slices
handles cow flags, and various cleanups

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

install -D -m 755 initscripts/sliceimage $RPM_BUILD_ROOT/%{_initrddir}/sliceimage
install -D -m 644 cron.d/sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/sliceimage
install -D -m 644 logrotate/sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/sliceimage

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_initrddir}/sliceimage
%{_sysconfdir}/cron.d/sliceimage
%{_sysconfdir}/logrotate.d/sliceimage

%post
chkconfig --add sliceimage
chkconfig sliceimage on
[ "$PL_BOOTCD" = "1" ] || service sliceimage start

# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/sliceimage

%post
# need to do this for system slices, for when a new image shows up
# we've already the service installed and enabled, as systemslices requires the plain package
[ "$PL_BOOTCD" = "1" ] || service sliceimage force

