#
# Conditional build:
%bcond_without	systemd		# without systemd support

%define		gitref	5aa50b12fc4bab29855edba8557f0ad8fe26e2d1
%define		snap	20230306
%define		rel	1

Summary:	TV streaming server
Name:		tvheadend
# https://tvheadend.org/projects/tvheadend/wiki/Releases
Version:	4.3.0
Release:	0.%{snap}.%{rel}
License:	GPL v3
Group:		Applications/Multimedia
Source0:	https://github.com/tvheadend/tvheadend/archive/%{gitref}/%{name}-%{snap}.tar.gz
# Source0-md5:	fcd2c9946c48ee9b112f9451b1c2ccdb
Source1:	%{name}.service
Source2:	%{name}.sysconfig
Source3:	%{name}.init
Patch0:		x32.patch
URL:		https://tvheadend.org/projects/tvheadend
BuildRequires:	avahi-devel
BuildRequires:	dbus-devel
BuildRequires:	ffmpeg-devel >= 3.0
BuildRequires:	gettext-tools
BuildRequires:	libdvbcsa-devel
BuildRequires:	libx264-devel
BuildRequires:	libx265-devel
BuildRequires:	openssl-devel
BuildRequires:	pcre2-8-devel
BuildRequires:	pkgconfig
BuildRequires:	python3-modules
BuildRequires:	rpmbuild(macros) >= 1.647
%{?with_systemd:BuildRequires:	systemd-devel}
BuildRequires:	uriparser-devel
BuildRequires:	zlib-devel
Requires(post):	sed >= 4.0
Requires(post,preun):	/sbin/chkconfig
%{?with_systemd:Requires(post,preun,postun):	systemd-units >= 38}
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/sbin/useradd
Requires:	setup
%{?with_systemd:Requires:	systemd-units >= 0.38}
Provides:	user(tvheadend)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Tvheadend is a TV streaming server for Linux supporting DVB-S, DVB-S2,
DVB-C, DVB-T, ATSC, IPTV, and Analog video (V4L) as input sources.

%prep
%setup -q -n %{name}-%{gitref}
%ifarch x32
%patch0 -p1
%endif

%{__sed} -i -e '1s,/usr/bin/env python3$,%{__python3},' lib/py/tvh/tv_meta_{tm,tv}db.py support/tvhmeta

%build
export CFLAGS="%{rpmcflags}"
export LDFLAGS="%{rpmldflags}"

# tvheadend uses a custom script, so %%configure cannot be used
# as not all options are supported
./configure \
	--cc="%{__cc}" \
	--release \
	--prefix=%{_prefix} \
	--libdir=%{_libdir} \
	--mandir=%{_mandir} \
	--python=%{__python3} \
	--disable-dvbscan \
	--disable-ffmpeg_static \
	--disable-hdhomerun_static \
	%{!?with_systemd:--disable-libsystemd_daemon}

%{__make} V=1

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/.hts/%{name} \
	$RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/Videos \
	%{?with_systemd:$RPM_BUILD_ROOT%{systemdunitdir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,sysconfig}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT \
        V=1

%{?with_systemd:cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service}
cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/%{name}
install -p %{SOURCE3} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}

chmod +x $RPM_BUILD_ROOT%{_bindir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%useradd -u 20 -d %{_localstatedir}/lib/%{name} -g video -G usb -c "tvheadend User" tvheadend

%post
/sbin/chkconfig --add tvheadend
%service tvheadend reload "tvheadend"
%{?with_systemd:%systemd_post %{name}.service}

%preun
if [ "$1" = "0" ]; then
	%service tvheadend stop
	/sbin/chkconfig --del tvheadend
fi
%{?with_systemd:%systemd_preun %{name}.service}

%postun
if [ "$1" = "0" ]; then
	%userremove tvheadend
fi
%{?with_systemd:%systemd_reload}

%files
%defattr(644,root,root,755)
%doc docs
%attr(755,root,root) %{_bindir}/%{name}
%attr(754,root,root) /etc/rc.d/init.d/tvheadend
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%{_mandir}/man1/%{name}.1*
%{_datadir}/%{name}
%{?with_systemd:%{systemdunitdir}/%{name}.service}

# home directory and config file
%dir %attr(755,tvheadend,root) %{_localstatedir}/lib/%{name}
%dir %attr(755,tvheadend,video) %{_localstatedir}/lib/%{name}/Videos
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts/%{name}
