%define name lxc-sliceimage
%define version 5.1
%define taglevel 2

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %{SCMURL}

Summary: lxc-specific node code for slice families
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires: btrfs-progs
BuildArch: noarch

%description
A simple package to deploy reference images for lxc

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
install -D -m 755 initscripts/lxc-sliceimage ${RPM_BUILD_ROOT}/%{_initrddir}/lxc-sliceimage
install -D -m 644 cron.d/lxc-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/lxc-sliceimage
install -D -m 644 logrotate/lxc-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/lxc-sliceimage
install -D -m 644 lxc_template.xml $RPM_BUILD_ROOT/vservers/.lvref/lxc_template.xml

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_initrddir}/lxc-sliceimage
%{_sysconfdir}/cron.d/lxc-sliceimage
%{_sysconfdir}/logrotate.d/lxc-sliceimage
/vservers/.lvref

%post
chkconfig --add lxc-sliceimage
chkconfig lxc-sliceimage on
# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/lxc-sliceimage
