%define name vserver-sliceimage
%define version 5.1
%define taglevel 4

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

install -D -m 755 initscripts/vserver-sliceimage $RPM_BUILD_ROOT/%{_initrddir}/vserver-sliceimage
install -D -m 644 cron.d/vserver-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/vserver-sliceimage
install -D -m 644 logrotate/vserver-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/vserver-sliceimage

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_initrddir}/vserver-sliceimage
%{_sysconfdir}/cron.d/vserver-sliceimage
%{_sysconfdir}/logrotate.d/vserver-sliceimage

%post
chkconfig --add vserver-sliceimage
chkconfig vserver-sliceimage on
# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/vserver-sliceimage
