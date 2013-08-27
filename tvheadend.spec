# TODO:
# - verify BR
#
%define		maj_version 3.4
%define		tar_subversion patch1
%define		min_version 27
######		Unknown group!
Summary:	TV streaming server
Name:		tvheadend
Version:	%{maj_version}.%{min_version}
Release:	0.2
License:	GPL v3
Group:		Video/Television
URL:		https://tvheadend.org/projects/tvheadend
Source0:	https://github.com/tvheadend/tvheadend/archive/%{maj_version}%{tar_subversion}.tar.gz
# Source0-md5:	86d1be0ad6e02bd2aecd3d529a026797
Source1:	%{name}.conf
Source2:	%{name}.service
Source3:	%{name}.sysconfig
#BuildRequires:	avahi-client-devel
#BuildRequires:	kdelibs4-devel
#BuildRequires:	libgcrypt-devel
#BuildRequires:	qt4-build
BuildRequires:	rpmbuild(macros) >= 1.647
Requires(post,preun,postun):	systemd-units >= 38
Requires:	systemd-units >= 0.38
Requires(post):	pwgen
Requires(post):	sed >= 4.0
Requires:	group(video)
Provides:	user(%{name})

%description
Tvheadend is a TV streaming server for Linux supporting DVB-S, DVB-S2,
DVB-C, DVB-T, ATSC, IPTV, and Analog video (V4L) as input sources.

%prep
%setup -q -n %{name}-%{maj_version}%{tar_subversion}

%build
#temporary workaround until upstream fixes compilation with gcc-4.6
#export CFLAGS="%{rpmcflags} -Wno-error=unused-but-set-variable"
export CFLAGS="%{rpmcflags}"
export CC="%{__cc}"
#tvheadend uses a custom configure script, so %%configure cannot be used
# as not all options are supported
./configure --prefix=%{_prefix} --release --libdir=%{_libdir} --mandir=%{_mandir}/man1 --disable-dvbscan
%{__make} V=1

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol \
	$RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/Videos \
	$RPM_BUILD_ROOT%{systemdunitdir} \
	$RPM_BUILD_ROOT/etc/sysconfig

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

cp %{SOURCE1} $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1
cp %{SOURCE2} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service
cp %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/%{name}

chmod +x $RPM_BUILD_ROOT%{_bindir}/%{name}

%pre
%useradd -u 20 -d %{_localstatedir}/lib/%{name} -g video -c "tvheadend User" %{name}

%post
%systemd_post %{name}.service

# check if the access control file still has the initial dummy password, and
# replace the dummy password by a random, 12-character pwgen-generated password
if  grep -q '"password": "dummypassword"' %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1; then
  sed -i "s,\"password\": \"dummypassword\",\"password\": \"$(pwgen -s 12 1)\"," %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1
fi

%preun
%systemd_preun %{name}.service

%postun
if [ "$1" = "0" ]; then
	%userremove %{name}
fi
%systemd_reload

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc docs
%attr(755,root,root) %{_bindir}/%{name}
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%{_mandir}/man1/%{name}.1*
%{_datadir}/%{name}
%{systemdunitdir}/%{name}.service

#home directory and config file
%dir %attr(755,tvheadend,root) %{_localstatedir}/lib/%{name}
%dir %attr(755,tvheadend,video) %{_localstatedir}/lib/%{name}/Videos
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts/%{name}
%dir %attr(750,tvheadend,video) %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol
%attr(600,tvheadend,video) %config(noreplace) %verify(not md5 mtime size) %{_localstatedir}/lib/%{name}/.hts/%{name}/accesscontrol/1

