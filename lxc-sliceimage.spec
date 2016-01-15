%define name lxc-sliceimage
%define version 5.1
%define taglevel 10

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
Requires: nodemanager-lxc >= 5.2-3
Requires: systemd
BuildArch: noarch

%description
A simple package to deploy reference images for lxc

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
install -D -m 755 bin/lxc-sliceimage ${RPM_BUILD_ROOT}/%{_bindir}/lxc-sliceimage
install -D -m 644 systemd/lxc-sliceimage.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system/lxc-sliceimage.service
install -D -m 644 cron.d/lxc-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/lxc-sliceimage
install -D -m 644 logrotate/lxc-sliceimage $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/lxc-sliceimage
install -D -m 644 lxc_template.xml $RPM_BUILD_ROOT/vservers/.lvref/lxc_template.xml

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/lxc-sliceimage
/usr/lib/systemd/system/lxc-sliceimage.service
%{_sysconfdir}/cron.d/lxc-sliceimage
%{_sysconfdir}/logrotate.d/lxc-sliceimage
/vservers/.lvref

# observed on a f23 node on jan-15-2016
# it feels like this call to restarting the service does not trigger
# or not reliably
# the daily crontab job should save the day though
# also just in case, we don't anymore disable the service when uninstalling either
%post
systemctl enable lxc-sliceimage.service
if [ "$PL_BOOTCD" != "1" ] ; then
   systemctl restart lxc-sliceimage.service
fi

# Randomize daily run time
M=$((60 * $RANDOM / 32768))
H=$((24 * $RANDOM / 32768))
sed -i -e "s/@M@/$M/" -e "s/@H@/$H/" %{_sysconfdir}/cron.d/lxc-sliceimage

