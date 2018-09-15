Summary:	TV streaming server
Name:		tvheadend
# https://tvheadend.org/projects/tvheadend/wiki/Releases
Version:	4.0.8
Release:	3
License:	GPL v3
Group:		Applications/Multimedia
Source0:	https://github.com/tvheadend/tvheadend/archive/v%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	dbb33a9b27a68749961f6aae700d9848
Source1:	%{name}.conf
Source2:	%{name}.service
Source3:	%{name}.sysconfig
Source4:	%{name}.init
Patch0:		x32.patch
Patch1:		ffmpeg3.patch
Patch2:		64bit.patch
Patch3:		32bit.patch
Patch4:		ffmpeg4.patch
Patch5:		no-Werror.patch
URL:		https://tvheadend.org/projects/tvheadend
BuildRequires:	avahi-devel
BuildRequires:	curl-devel
BuildRequires:	ffmpeg-devel
BuildRequires:	python-modules
BuildRequires:	rpmbuild(macros) >= 1.647
BuildRequires:	uriparser-devel
BuildRequires:	zlib-devel
Requires(post):	pwgen
Requires(post):	sed >= 4.0
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/sbin/useradd
Requires:	setup
Requires:	systemd-units >= 0.38
Provides:	user(tvheadend)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Tvheadend is a TV streaming server for Linux supporting DVB-S, DVB-S2,
DVB-C, DVB-T, ATSC, IPTV, and Analog video (V4L) as input sources.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%ifarch %{x8664}
%patch2 -p1
%endif
%ifarch %{ix86} x32
%patch3 -p1
%endif
%patch4 -p1
%patch5 -p1

%build
export CFLAGS="%{rpmcflags}"
export CC="%{__cc}"

# tvheadend uses a custom script, so %%configure cannot be used
# as not all options are supported
./configure \
	--release \
	--prefix=%{_prefix} \
	--libdir=%{_libdir} \
	--mandir=%{_mandir} \
	--disable-dvbscan

%{__make} V=1

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol \
	$RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/Videos \
	$RPM_BUILD_ROOT%{systemdunitdir} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,sysconfig}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

cp -p %{SOURCE1} $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1
cp -p %{SOURCE2} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/%{name}
install -p %{SOURCE4} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}

chmod +x $RPM_BUILD_ROOT%{_bindir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%useradd -u 20 -d %{_localstatedir}/lib/%{name} -g video -G usb -c "tvheadend User" tvheadend

%post
/sbin/chkconfig --add tvheadend
%service tvheadend reload "tvheadend"
%systemd_post %{name}.service

# check if the access control file still has the initial dummy password, and
# replace the dummy password by a random, 12-character pwgen-generated password
if  grep -q '"password": "dummypassword"' %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1; then
	sed -i "s,\"password\": \"dummypassword\",\"password\": \"$(pwgen -s 12 1)\"," %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1
fi

%preun
if [ "$1" = "0" ]; then
	%service tvheadend stop
	/sbin/chkconfig --del tvheadend
fi
%systemd_preun %{name}.service

%postun
if [ "$1" = "0" ]; then
	%userremove tvheadend
fi
%systemd_reload

%files
%defattr(644,root,root,755)
%doc docs
%attr(755,root,root) %{_bindir}/%{name}
%attr(754,root,root) /etc/rc.d/init.d/tvheadend
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%{_mandir}/man1/%{name}.1*
%{_datadir}/%{name}
%{systemdunitdir}/%{name}.service

# home directory and config file
%dir %attr(755,tvheadend,root) %{_localstatedir}/lib/%{name}
%dir %attr(755,tvheadend,video) %{_localstatedir}/lib/%{name}/Videos
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts/%{name}
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol
%attr(600,tvheadend,video) %config(noreplace) %verify(not md5 mtime size) %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1
