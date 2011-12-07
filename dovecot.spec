%global betasuffix .beta6
%global snapsuffix 20100630

Summary: Secure imap and pop3 server
Name: dovecot
Epoch: 1
Version: 2.0
Release: 0.10%{?betasuffix}.%{?snapsuffix}%{?dist}
#dovecot itself is MIT, a few sources are PD, pigeonhole is LGPLv2
License: MIT and LGPLv2
Group: System Environment/Daemons

%define pigeonhole_version 20100516

URL: http://www.dovecot.org/
#Source: http://www.dovecot.org/releases/2.0/beta/%{name}-%{version}%{?betasuffix}%{?snapsuffix}.tar.gz
#we use nightly snapshots for now: 
Source: http://www.dovecot.org/nightly/%{name}-%{snapsuffix}.tar.gz
Source1: dovecot.init
Source2: dovecot.pam
#Source8: http://hg.rename-it.nl/dovecot-2.0-pigeonhole/archive/tip.tar.bz2
#we use this ^^^ repository snapshost just renamed to contain last commit in name
%global phsnap 1def8519d775
Source8: pigeonhole-snap%{phsnap}.tar.bz2
Source9: dovecot.sysconfig

#our own
Source14: dovecot.conf.5

# 3x Fedora/RHEL specific
Patch1: dovecot-2.0-defaultconfig.patch
Patch2: dovecot-1.0.beta2-mkcert-permissions.patch
Patch3: dovecot-1.0.rc7-mkcert-paths.patch

#fix sieve initialization, for pigeonhole<703f82bb2b09 or <=20100708, rhbz#612942
Patch4: dovecot-2.0-fixinitcrash.patch

Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: openssl-devel, pam-devel, zlib-devel, bzip2-devel, libcap-devel
BuildRequires: libtool, autoconf, automake, pkgconfig
BuildRequires: sqlite-devel
BuildRequires: postgresql-devel
BuildRequires: mysql-devel
BuildRequires: openldap-devel
BuildRequires: krb5-devel

# gettext-devel is needed for running autoconf because of the
# presence of AM_ICONV
BuildRequires: gettext-devel

# Explicit Runtime Requirements for executalbe
Requires: openssl >= 0.9.7f-4

# Package includes an initscript service file, needs to require initscripts package
Requires: initscripts
Requires(pre): shadow-utils
Requires(post): chkconfig shadow-utils
Requires(preun): shadow-utils chkconfig initscripts
Requires(postun): initscripts

%define ssldir %{_sysconfdir}/pki/%{name}

%description
Dovecot is an IMAP server for Linux/UNIX-like systems, written with security 
primarily in mind.  It also contains a small POP3 server.  It supports mail 
in either of maildir or mbox formats.

The SQL drivers and authentication plug-ins are in their subpackages.

%package pigeonhole
Requires: %{name} = %{epoch}:%{version}-%{release}
Obsoletes: dovecot-sieve < 1:1.2.10-3
Obsoletes: dovecot-managesieve < 1:1.2.10-3
Summary: Sieve and managesieve plug-in for dovecot
Group: System Environment/Daemons
License: MIT and LGPLv2

%description pigeonhole
This package provides sieve and managesieve plug-in for dovecot LDA.

%package pgsql
Requires: %{name} = %{epoch}:%{version}-%{release}
Summary: Postgres SQL back end for dovecot
Group: System Environment/Daemons
%description pgsql
This package provides the Postgres SQL back end for dovecot-auth etc.

%package mysql
Requires: %{name} = %{epoch}:%{version}-%{release}
Summary: MySQL back end for dovecot
Group: System Environment/Daemons
%description mysql
This package provides the MySQL back end for dovecot-auth etc.

%package devel
Requires: %{name} = %{epoch}:%{version}-%{release}
Summary: Development files for dovecot
Group: Development/Libraries
%description devel
This package provides the development files for dovecot.

%prep
%setup -q -n %{name}-%{version}%{?betasuffix}
%setup -q  -n %{name}-%{version}%{?betasuffix} -D -T -a 8 

%patch1 -p1 -b .default-settings
%patch2 -p1 -b .mkcert-permissions
%patch3 -p1 -b .mkcert-paths
%patch4 -p1 -b .fixinitcrash

%build
#autotools hacks can be removed later, nightly does not support --docdir
aclocal -I . --force
libtoolize --copy --force
autoconf --force
autoheader --force
automake --add-missing --copy --force-missing
#required for fdpass.c line 125,190: dereferencing type-punned pointer will break strict-aliasing rules
export CFLAGS="$RPM_OPT_FLAGS -fno-strict-aliasing"
%configure                       \
    INSTALL_DATA="install -c -p -m644" \
    --docdir=%{_docdir}/%{name}-%{version}     \
    --disable-static             \
    --disable-rpath              \
    --with-nss                   \
    --with-shadow                \
    --with-pam                   \
    --with-gssapi=plugin         \
    --with-ldap=plugin           \
    --with-sql=plugin            \
    --with-pgsql                 \
    --with-mysql                 \
    --with-sqlite                \
    --with-zlib                  \
    --with-libcap                \
    --with-ssl=openssl           \
    --with-ssldir=%{ssldir}      \
    --with-docs

sed -i 's|/etc/ssl|/etc/pki/dovecot|' doc/mkcert.sh doc/example-config/conf.d/10-ssl.conf

make %{?_smp_mflags}

#pigeonhole
pushd dovecot-2-0-pigeonhole-%{phsnap}
autoreconf -fiv
%configure                             \
    INSTALL_DATA="install -c -p -m644" \
    --disable-static                   \
    --with-dovecot=../                 \
    --without-unfinished-features

make %{?_smp_mflags}
popd

%install
rm -rf $RPM_BUILD_ROOT

make install DESTDIR=$RPM_BUILD_ROOT

pushd dovecot-2-0-pigeonhole-%{phsnap}
make install DESTDIR=$RPM_BUILD_ROOT
popd

#move doc dir back to build dir so doc macro in files section can use it
mv $RPM_BUILD_ROOT/%{_docdir}/%{name}-%{version} %{_builddir}/%{name}-%{version}%{?betasuffix}/docinstall

install -p -D -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_initddir}/dovecot

install -p -D -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/dovecot

install -p -D -m 600 %{SOURCE9} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/dovecot

#install man pages
install -p -D -m 644 %{SOURCE14} $RPM_BUILD_ROOT%{_mandir}/man5/dovecot.conf.5

# generate ghost .pem files
mkdir -p $RPM_BUILD_ROOT%{ssldir}/certs
mkdir -p $RPM_BUILD_ROOT%{ssldir}/private
touch $RPM_BUILD_ROOT%{ssldir}/certs/dovecot.pem
chmod 600 $RPM_BUILD_ROOT%{ssldir}/certs/dovecot.pem
touch $RPM_BUILD_ROOT%{ssldir}/private/dovecot.pem
chmod 600 $RPM_BUILD_ROOT%{ssldir}/private/dovecot.pem

mkdir -p $RPM_BUILD_ROOT/var/run/dovecot/{empty,login}
chmod 755 $RPM_BUILD_ROOT/var/run/dovecot
chmod 700 $RPM_BUILD_ROOT/var/run/dovecot/login

# Install dovecot configuration and dovecot-openssl.cnf
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/dovecot/conf.d
install -p -m 644 docinstall/example-config/dovecot.conf $RPM_BUILD_ROOT%{_sysconfdir}/dovecot
install -p -m 644 docinstall/example-config/conf.d/*.conf $RPM_BUILD_ROOT%{_sysconfdir}/dovecot/conf.d
install -p -m 644 docinstall/example-config/conf.d/*.conf.ext $RPM_BUILD_ROOT%{_sysconfdir}/dovecot/conf.d
install -p -m 644 doc/dovecot-openssl.cnf $RPM_BUILD_ROOT%{ssldir}/dovecot-openssl.cnf

install -p -m755 doc/mkcert.sh $RPM_BUILD_ROOT%{_libexecdir}/%{name}/mkcert.sh

mkdir -p $RPM_BUILD_ROOT/var/lib/dovecot

#remove the libtool archives
find $RPM_BUILD_ROOT%{_libdir}/%{name}/ -name '*.la' | xargs rm -f

#remove what we don't want
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/dovecot/README
pushd docinstall
rm -f securecoding.txt thread-refs.txt
popd


%clean
rm -rf $RPM_BUILD_ROOT


%pre
#dovecot uig and gid are reserved, see /usr/share/doc/setup-*/uidgid
getent group dovecot >/dev/null || groupadd -r --gid 97 dovecot
getent passwd dovecot >/dev/null || \
useradd -r --uid 97 -g dovecot -d /usr/libexec/dovecot -s /sbin/nologin -c "Dovecot IMAP server" dovecot

getent group dovenull >/dev/null || groupadd -r dovenull
getent passwd dovenull >/dev/null || \
useradd -r -g dovenull -d /usr/libexec/dovecot -s /sbin/nologin -c "Dovecot's unauthorized user" dovenull
exit 0

%post
/sbin/chkconfig --add %{name}
# generate the ssl certificates
if [ ! -f %{ssldir}/certs/%{name}.pem ]; then
    SSLDIR=%{ssldir} OPENSSLCONFIG=%{ssldir}/dovecot-openssl.cnf \
         %{_libexecdir}/%{name}/mkcert.sh &> /dev/null
fi

if ! test -f /var/run/dovecot/login/ssl-parameters.dat; then
    dovecot --build-ssl-parameters &>/dev/null
fi
exit 0

%preun
if [ $1 = 0 ]; then
    /sbin/service %{name} stop > /dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%postun
if [ "$1" -ge "1" ]; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi

%check
make check
cd dovecot-2-0-pigeonhole-%{phsnap}
make test

%files
%defattr(-,root,root,-)
%doc docinstall/* AUTHORS ChangeLog COPYING COPYING.LGPL COPYING.MIT NEWS README
%{_sbindir}/dovecot

%{_bindir}/doveadm
%{_bindir}/doveconf
%{_bindir}/dsync

%dir %{_sysconfdir}/dovecot
%dir %{_sysconfdir}/dovecot/conf.d
%config(noreplace) %{_sysconfdir}/dovecot/dovecot.conf
#list all so we'll be noticed if upstream changes anything
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-auth.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-director.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-logging.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-mail.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-master.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/10-ssl.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/15-lda.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/20-imap.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/20-lmtp.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/20-pop3.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/90-acl.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/90-quota.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/90-plugin.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-checkpassword.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-deny.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-ldap.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-master.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-passwdfile.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-sql.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-static.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-system.conf.ext
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/auth-vpopmail.conf.ext

%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/dovecot
%config(noreplace) %{_sysconfdir}/pam.d/dovecot
%config(noreplace) %{ssldir}/dovecot-openssl.cnf

%{_initddir}/dovecot

%dir %{ssldir}
%dir %{ssldir}/certs
%dir %{ssldir}/private
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{ssldir}/certs/dovecot.pem
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{ssldir}/private/dovecot.pem

%dir %{_libdir}/dovecot
%dir %{_libdir}/dovecot/auth
%dir %{_libdir}/dovecot/dict
%{_libdir}/dovecot/doveadm
#these are plugins (*.so files) not a devel files
%{_libdir}/dovecot/*_plugin.so
%{_libdir}/dovecot/*.so.*
%{_libdir}/dovecot/auth/libauthdb_ldap.so
%{_libdir}/dovecot/auth/libmech_gssapi.so
%{_libdir}/dovecot/auth/libdriver_sqlite.so
%{_libdir}/dovecot/dict/libdriver_sqlite.so
%{_libdir}/dovecot/libdriver_sqlite.so

%{_libexecdir}/dovecot

%attr(0755,root,dovecot) %dir /var/run/dovecot
%dir /var/run/dovecot/empty
%attr(0750,root,dovenull) %dir /var/run/dovecot/login
%attr(0750,dovecot,dovecot) %dir /var/lib/dovecot

%{_mandir}/man1/deliver.1.gz
%{_mandir}/man1/doveadm*.1.gz
%{_mandir}/man1/doveconf.1.gz
%{_mandir}/man1/dovecot*.1.gz
%{_mandir}/man1/dsync.1.gz
%{_mandir}/man5/dovecot.conf.5.gz
%{_mandir}/man7/doveadm-search-query.7.gz

%files devel
%defattr(-,root,root,-)
%{_includedir}/dovecot
%{_datadir}/aclocal/dovecot.m4
%{_libdir}/dovecot/libdovecot*.so
%{_libdir}/dovecot/dovecot-config

%files pigeonhole
%defattr(-,root,root,-)
%{_bindir}/sieve-test
%{_bindir}/sievec
%{_bindir}/sieved
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/90-sieve.conf
%config(noreplace) %{_sysconfdir}/dovecot/conf.d/20-managesieve.conf
%{_libexecdir}/%{name}/managesieve
%{_libexecdir}/%{name}/managesieve-login

%dir %{_libdir}/dovecot/settings
%{_libdir}/dovecot/settings/libmanagesieve_*.so

%{_mandir}/man1/sieve-test.1.gz
%{_mandir}/man1/sievec.1.gz
%{_mandir}/man1/sieved.1.gz

%files mysql
%defattr(-,root,root,-)
%{_libdir}/%{name}/libdriver_mysql.so
%{_libdir}/%{name}/auth/libdriver_mysql.so
%{_libdir}/%{name}/dict/libdriver_mysql.so

%files pgsql
%defattr(-,root,root,-)
%{_libdir}/%{name}/libdriver_pgsql.so
%{_libdir}/%{name}/auth/libdriver_pgsql.so
%{_libdir}/%{name}/dict/libdriver_pgsql.so

%changelog
* Mon Jul 19 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.10.beta6.20100630
- last fix fixed reproducer, but was incomplete

* Thu Jul 15 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.9.beta6.20100630
- fix crash of sieve plugin initialization

* Wed Jun 30 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.8.beta6.20100630
- dovecot and pigeonhole updated
- moved disable_plaintext_auth to 10-auth.conf
- moved ACL and quota settings to a separate .conf files

* Wed May 26 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.7.beta6.20100515
- fix: some code is not compatible with strict aliasing

* Thu May 20 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.6.beta6.20100515
- use reserved uid and gid for dovecot user and group
- create /var/run/dovecot/empty in advance in rpm

* Tue May 18 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.5.beta5.20100515
- dovenull is unauthorized user, needs own dovenull group

* Tue May 18 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.4.beta5.20100515
- fix typo in dovenull username

* Tue May 18 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.3.beta5.20100515
- pigeonhole and dovecot updated to snapshot 20100515
- fix crash for THREAD command

* Fri May 07 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.2.beta4.20100506
- fix lincense

* Thu May 06 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:2.0-0.1.beta4.20100506
- dovecot updated to 2.0 post beta4 snapshot 20100506

* Thu Mar 11 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.9-4
- mbox, dbox, cydir: Make sure mail root directory is created with 0700
  permissions
- mbox: Message header reading was unnecessarily slow. Fetching a
  huge header could have resulted in Dovecot eating a lot of CPU.
  Also searching messages was much slower than necessary
- resolves: #572276

* Fri Feb 19 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.9-3
- simplify packaging
- merged dovecot-sieve and dovecot-managesieve into dovecot-pigeonhole
- merged dovecot-sqlite, dovecot-gssapi and dovecot-ldap into dovecot

* Wed Jan 06 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.9-2
- cleanup : remove obsoleted doc

* Fri Dec 18 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.9-1
- sieve updated to 0.1.14
- managesieve updated to 0.11.10 
- updated to 1.2.9
- maildir: When saving, filenames now always contain ,S=<size>.
  Previously this was done only when quota plugin was loaded. It's
  required for zlib plugin and may be useful for other things too.
- maildir: v1.2.7 and v1.2.8 caused assert-crashes in
  maildir_uidlist_records_drop_expunges()
- maildir_copy_preserve_filename=yes could have caused crashes.
- Maildir++ quota: % limits weren't updated when limits were read
  from maildirsize.
- virtual: v1.2.8 didn't fully fix the "lots of mailboxes" bug
- virtual: Fixed updating virtual mailbox based on flag changes.
- fts-squat: Fixed searching multi-byte characters.

* Tue Nov 24 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.8-3
- fix dovecot's restart after update (#518753)

* Tue Nov 24 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.8-2
- fix initdddir typo (for rhel rebuilds)

* Fri Nov 20 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.8-1
- update to dovecot 1.2.8

* Mon Nov 16 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.7-2
- use originall managesieve to dovecot diff
- EPEL-ize spec for rhel5 rebuilds (#537666)

* Fri Nov 13 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.7-1
- updated to dovecot 1.2.7
- add man pages
- IMAP: IDLE now sends "Still here" notifications to same user's
  connections at the same time. This hopefully reduces power usage
  of some mobile clients that use multiple IDLEing connections.
- IMAP: If imap_capability is set, show it in the login banner.
- IMAP: Implemented SORT=DISPLAY extension.
- Login process creation could have sometimes failed with epoll_ctl()
  errors or without epoll probably some other strange things could
  have happened.
- Maildir: Fixed some performance issues
- Maildir: Fixed crash when using a lot of keywords.
- Several fixes to QRESYNC extension and modseq handling
- mbox: Make sure failed saves get rolled back with NFS.
- dbox: Several fixes.

* Mon Nov 02 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.6-5
- spec cleanup

* Wed Oct 21 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.6-4
- imap-login: If imap_capability is set, show it in the banner 
  instead of the default (#524485)

* Mon Oct 19 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.6-3
- sieve updated to 0.1.13 which brings these changes:
- Body extension: implemented proper handling of the :raw transform
  and added various new tests to the test suite. However, :content
  "multipart" and :content "message/rfc822" are still not working.
- Fixed race condition occuring when multiple instances are saving the
  same binary (patch by Timo Sirainen).
- Body extension: don't give SKIP_BODY_BLOCK flag to message parser,
  we want the body!
- Fixed bugs in multiscript support; subsequent keep actions were not
  always merged correctly and implicit side effects were not always
  handled correctly.
- Fixed a segfault bug in the sieve-test tool occuring when compile
  fails.
- Fixed segfault bug in action procesing. It was triggered while
  merging side effects in duplicate actions.
- Fixed bug in the Sieve plugin that caused it to try to stat() a NULL
  path, yielding a 'Bad address' error.

* Fri Oct 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.6-2
- fix init script for case when no action was specified

* Tue Oct 06 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.6-1
- dovecot updated to 1.2.6
- Added authtest utility for doing passdb and userdb lookups.
- login: ssl_security string now also shows the used compression.
- quota: Don't crash with non-Maildir++ quota backend.
- imap proxy: Fixed crashing with some specific password characters.
- fixed broken dovecot --exec-mail.
- Avoid assert-crashing when two processes try to create index at the
  same time.

* Tue Sep 29 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.5-2
- build with libcap enabled

* Thu Sep 17 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.5-1
- updated to dovecot 1.2.5
- Authentication: DIGEST-MD5 and RPA mechanisms no longer require
  user's login realm to be listed in auth_realms. It only made
  configuration more difficult without really providing extra security.
- zlib plugin: Don't allow clients to save compressed data directly.
  This prevents users from exploiting (most of the) potential security
  holes in zlib/bzlib.
- fix index file handling that could have caused an assert-crash
- IMAP: Fixes to QRESYNC extension.
- deliver: Don't send rejects to any messages that have Auto-Submitted
  header. This avoids emails loops.

* Wed Sep 16 2009 Tomas Mraz <tmraz@redhat.com> - 1:1.2.4-3
- use password-auth common PAM configuration instead of system-auth

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 1:1.2.4-2
- rebuilt with new openssl

* Fri Aug 21 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.4-1
- updated: dovecot 1.2.4, managesieve 0.11.9, sieve 0.1.12
- fixed a crash in index file handling
- fixed a crash in saving messages where message contained a CR
  character that wasn't followed by LF
- fixed a crash when listing shared namespace prefix
- sieve: implemented the new date extension. This allows matching
  against date values in header fields and the current date at
  the time of script evaluation
- managesieve: reintroduced ability to abort SASL with "*" response

* Mon Aug 10 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.3-1
- updated: dovecot 1.2.3, managesieve 0.11.8, sieve 0.1.11
- Mailbox names with control characters can't be created anymore.
  Existing mailboxes can still be accessed though.
- Allow namespace prefix to be opened as mailbox, if a mailbox
  already exists in the root dir.
- Maildir: dovecot-uidlist was being recreated every time a mailbox
  was accessed, even if nothing changed.
- listescape plugin was somewhat broken
- ldap: Fixed hang when >128 requests were sent at once.
- fts_squat: Fixed crashing when searching virtual mailbox.
- imap: Fixed THREAD .. INTHREAD crashing.

* Tue Jul 28 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.2-1.20090728snap
- updated to post 1.2.2 snapshot (including post release GSSAPI fix)
- Fixed "corrupted index cache file" errors
- IMAP: FETCH X-* parameters weren't working.
- Maildir++ quota: Quota was sometimes updated wrong
- Dovecot master process could hang if it received signals too rapidly

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.2.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 23 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.1-2
- updated sieve plugin to 0.1.9

* Mon Jul 13 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2.1-1
- updated to 1.2.1
- GSSAPI authentication is fixed (#506782)
- logins now fail if home directory path is relative, because it was 
  not working correctly and never was expected to work
- sieve and managesieve update

* Mon Apr 20 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2-0.rc3.1
- updated to 1.2.rc3

* Mon Apr 06 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2-0.rc2.1
- updated to 1.2.rc2

* Mon Mar 30 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2-0.beta4.2
- fix typo and rebuild

* Mon Mar 30 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.2-0.beta4.1
- spec clean-up
- updated to 1.2.beta4

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.1.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Feb 11 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.11-1
- updated to 1.1.11
- IMAP: PERMANENTFLAGS list didn't contain \*, causing some clients
  not to save keywords.
- auth: Using "username" or "domain" passdb fields caused problems
  with cache and blocking passdbs in v1.1.8 .. v1.1.10.   
- userdb prefetch + blocking passdbs was broken with non-plaintext
  auth in v1.1.8 .. v1.1.10.

* Tue Jan 27 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.10-1
- updated to 1.1.10

* Sat Jan 24 2009 Dan Horak <dan[at]danny.cz> - 1:1.1.8-3
- rebuild with new mysql

* Tue Jan 13 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.8-2
- added managesieve support (thanks Helmut K. C. Tessarek)

* Thu Jan 8 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.8-1
- dovecot updated to 1.1.8
- sieve-plugin updated to 1.1.6

* Tue Dec 2 2008 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.7-2
- revert changes from 1:1.1.6-2 and 1:1.1.6-1
- password can be stored in different file readable only for root 
  via !include_try directive

* Tue Dec 2 2008 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.7-1
- update to upstream version 1.1.7

* Mon Nov 3 2008 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.6-2
- changed comment in sysconfig to match actual state

* Mon Nov 3 2008 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.6-1
- update to upstream version 1.1.6
- change permissions of deliver and dovecot.conf to prevent possible password exposure

* Wed Oct 29 2008 Michal Hlavinka <mhlavink@redhat.com> - 1:1.1.5-1
- update to upstream version 1.1.5 (Resolves: CVE-2008-4577, CVE-2008-4578)

* Tue Sep  2 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.3-1
- update to upstream version 1.1.3

* Tue Jul 29 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.2-2
- really ask for the password during start-up

* Tue Jul 29 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.2-1
- update to upstream version 1.1.2
- final solution for #445200 (add /etc/sysconfig/dovecot for start-up options)

* Fri Jun 27 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.1-2
- update default settings to listen on both IPv4 and IPv6 instead of IPv6 only

* Sun Jun 22 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.1-1
- update to upstream version 1.1.1

* Sat Jun 21 2008 Dan Horak <dan[at]danny.cz> - 1:1.1.0-1
- update to upstream version 1.1.0
- update sieve plugin to 1.1.5
- remove unnecessary patches
- enable ldap and gssapi plugins
- change ownership of dovecot.conf (Resolves: #452088)

* Wed Jun 18 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.14-4
- update init script (Resolves: #451838)

* Fri Jun  6 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.14-3
- build devel subpackage (Resolves: #306881)

* Thu Jun  5 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.14-2
- install convert-tool (Resolves: #450010)

* Tue Jun  3 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.14-1
- update to upstream version 1.0.14
- remove setcred patch (use of setcred must be explictly enabled in config)

* Thu May 29 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.13-8
- update scriptlets to follow UsersAndGroups guideline
- remove support for upgrading from version < 1.0 from scriptlets
- Resolves: #448095

* Tue May 20 2008 Dan Horak <dan[at]danny.cz> - 1:1.0.13-7
- spec file cleanup
- update sieve plugin to 1.0.3
- Resolves: #445200, #238018

* Sun Mar 09 2008 Tomas Janousek <tjanouse@redhat.com> - 1:1.0.13-6
- update to latest upstream stable (1.0.13)

* Wed Feb 20 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1:1.0.10-5
- Autorebuild for GCC 4.3

* Fri Jan 07 2008 Tomas Janousek <tjanouse@redhat.com> - 1:1.0.10-4
- update to latest upstream stable (1.0.10)

* Wed Dec 05 2007 Jesse Keating <jkeating@redhat.com> - 1:1.0.7-3
- Bump for deps

* Mon Nov 05 2007 Tomas Janousek <tjanouse@redhat.com> - 1:1.0.7-2
- update to latest upstream stable (1.0.7)
- added the winbind patch (#286351)

* Tue Sep 25 2007 Tomas Janousek <tjanouse@redhat.com> - 1:1.0.5-1
- downgraded to lastest upstream stable (1.0.5)

* Wed Aug 22 2007 Tomas Janousek <tjanouse@redhat.com> - 1.1-16.1.alpha3
- updated license tags

* Mon Aug 13 2007 Tomas Janousek <tjanouse@redhat.com> - 1.1-16.alpha3
- updated to latest upstream alpha
- update dovecot-sieve to 0367450c9382 from hg

* Fri Aug 10 2007 Tomas Janousek <tjanouse@redhat.com> - 1.1-15.alpha2
- updated to latest upstream alpha
- split ldap and gssapi plugins to subpackages

* Wed Jul 25 2007 Tomas Janousek <tjanouse@redhat.com> - 1.1-14.6.hg.a744ae38a9e1
- update to a744ae38a9e1 from hg
- update dovecot-sieve to 131e25f6862b from hg and enable it again

* Thu Jul 19 2007 Tomas Janousek <tjanouse@redhat.com> - 1.1-14.5.alpha1
- update to latest upstream alpha
- don't build dovecot-sieve, it's only for 1.0

* Sun Jul 15 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0.2-13.5
- update to latest upstream

* Mon Jun 18 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0.1-12.5
- update to latest upstream

* Fri Jun 08 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0.0-11.7
- specfile merge from 145241 branch
    - new sql split patch
    - support for not building all sql modules
    - split sql libraries to separate packages

* Sat Apr 14 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0.0-11.1
- dovecot-1.0.beta2-pam-tty.patch is no longer needed

* Fri Apr 13 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0.0-11
- update to latest upstream

* Tue Apr 10 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-10.rc31
- update to latest upstream

* Fri Apr 06 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-9.rc30
- update to latest upstream

* Fri Mar 30 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-8.1.rc28
- spec file cleanup (fixes docs path)

* Fri Mar 23 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-8.rc28
- update to latest upstream

* Mon Mar 19 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-7.rc27
- use dovecot-sieve's version for the package

* Mon Mar 19 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-6.rc27
- update to latest upstream
- added dovecot-sieve

* Fri Mar 02 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-5.rc25
- update to latest upstream

* Sun Feb 25 2007 Jef Spaleta <jspaleta@gmail.com> - 1.0-4.rc22
- Merge review changes

* Thu Feb 08 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-3.rc22
- update to latest upstream, fixes a few bugs

* Mon Jan 08 2007 Tomas Janousek <tjanouse@redhat.com> - 1.0-2.rc17
- update to latest upstream, fixes a few bugs

* Thu Dec 21 2006 Tomas Janousek <tjanouse@redhat.com> - 1.0-1.1.rc15
- reenabled GSSAPI (#220377)

* Tue Dec 05 2006 Tomas Janousek <tjanouse@redhat.com> - 1.0-1.rc15
- update to latest upstream, fixes a few bugs, plus a security
  vulnerability (#216508, CVE-2006-5973)

* Tue Oct 10 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.3.rc7
- fix few inconsistencies in specfile, fixes #198940

* Wed Oct 04 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.2.rc7
- fix default paths in the example mkcert.sh to match configuration
  defaults (fixes #183151)

* Sun Oct 01 2006 Jesse Keating <jkeating@redhat.com> - 1.0-0.1.rc7
- rebuilt for unwind info generation, broken in gcc-4.1.1-21

* Fri Sep 22 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.rc7
- update to latest upstream release candidate, should fix occasional
  hangs and mbox issues... INBOX. namespace is still broken though
- do not run over symlinked certificates in new locations on upgrade

* Tue Aug 15 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.rc2.2
- include /var/lib/dovecot in the package, prevents startup failure
  on new installs

* Mon Jul 17 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.rc2.1
- reenable inotify and see what happens

* Thu Jul 13 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.rc2
- update to latest upstream release candidate
- disable inotify for now, doesn't build -- this needs fixing though

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 1.0-0.beta8.2.1
- rebuild

* Thu Jun 08 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta8.2
- put back pop3_uidl_format default that got lost
  in the beta2->beta7 upgrade (would cause pop3 to not work
  at all in many situations)

* Thu May 04 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta8.1
- upgrade to latest upstream beta release (beta8)
- contains a security fix in mbox handling

* Thu May 04 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta7.1
- upgrade to latest upstream beta release
- fixed BR 173048

* Fri Mar 17 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.8
- fix sqlite detection in upstream configure checks, second part
  of #182240

* Wed Mar  8 2006 Bill Nottingham <notting@redhat.com> - 1.0-0.beta2.7
- fix scriplet noise some more

* Mon Mar  6 2006 Jeremy Katz <katzj@redhat.com> - 1.0-0.beta2.6
- fix scriptlet error (mitr, #184151)

* Mon Feb 27 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.5
- fix #182240 by looking in lib64 for libs first and then lib
- fix comment #1 in #182240 by copying over the example config files
  to documentation directory

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 1.0-0.beta2.4.1
- bump again for double-long bug on ppc(64)

* Thu Feb 09 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.4
- enable inotify as it should work now (#179431)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 1.0-0.beta2.3.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Feb 02 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.3
- change the compiled-in defaults and adjust the default's configfile
  commented-out example settings to match compiled-in defaults,
  instead of changing the defaults only in the configfile, as per #179432
- fix #179574 by providing a default uidl_format for pop3
- half-fix #179620 by having plaintext auth enabled by default... this
  needs more thinking (which one we really want) and documentation
  either way

* Tue Jan 31 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.2
- update URL in description
- call dovecot --build-ssl-parameters in postinst as per #179430

* Mon Jan 30 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2.1
- fix spec to work with BUILD_DIR != SOURCE_DIR
- forward-port and split pam-nocred patch

* Mon Jan 23 2006 Petr Rockai <prockai@redhat.com> - 1.0-0.beta2
- new upstream version, hopefully fixes #173928, #163550
- fix #168866, use install -p to install documentation

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Sat Nov 12 2005 Tom Lane <tgl@redhat.com> - 0.99.14-10.fc5
- Rebuild due to mysql update.

* Wed Nov  9 2005 Tomas Mraz <tmraz@redhat.com> - 0.99.14-9.fc5
- rebuilt with new openssl

* Fri Sep 30 2005 Tomas Mraz <tmraz@redhat.com> - 0.99.14-8.fc5
- use include instead of pam_stack in pam config

* Wed Jul 27 2005 John Dennis <jdennis@redhat.com> - 0.99.14-7.fc5
- fix bug #150888, log authenication failures with ip address

* Fri Jul 22 2005 John Dennis <jdennis@redhat.com> - 0.99.14-6.fc5
- fix bug #149673, add dummy PAM_TTY

* Thu Apr 28 2005 John Dennis <jdennis@redhat.com> - 0.99.14-5.fc4
- fix bug #156159 insecure location of restart flag file

* Fri Apr 22 2005 John Dennis <jdennis@redhat.com> - 0.99.14-4.fc4
- openssl moved its certs, CA, etc. from /usr/share/ssl to /etc/pki

* Tue Apr 12 2005 Tom Lane <tgl@redhat.com> 0.99.14-3.fc4
- Rebuild for Postgres 8.0.2 (new libpq major version).

* Mon Mar  7 2005 John Dennis <jdennis@redhat.com> 0.99.14-2.fc4
- bump rev for gcc4 build

* Mon Feb 14 2005 John Dennis <jdennis@redhat.com> - 0.99.14-1.fc4
- fix bug #147874, update to 0.99.14 release
  v0.99.14 2005-02-11  Timo Sirainen <tss at iki.fi>
  - Message address fields are now parsed differently, fixing some
    issues with spaces. Affects only clients which use FETCH ENVELOPE
    command.
  - Message MIME parser was somewhat broken with missing MIME boundaries
  - mbox: Don't allow X-UID headers in mails to override the UIDs we
    would otherwise set. Too large values can break some clients and
    cause other trouble.
  - passwd-file userdb wasn't working
  - PAM crashed with 64bit systems
  - non-SSL inetd startup wasn't working
  - If UID FETCH notices and skips an expunged message, don't return
    a NO reply. It's not needed and only makes clients give error
    messages.

* Wed Feb  2 2005 John Dennis <jdennis@redhat.com> - 0.99.13-4.devel
- fix bug #146198, clean up temp kerberos tickets

* Mon Jan 17 2005 John Dennis <jdennis@redhat.com> 0.99.13-3.devel
- fix bug #145214, force mbox_locks to fcntl only
- fix bug #145241, remove prereq on postgres and mysql, allow rpm auto
  dependency generator to pick up client lib dependency if needed.

* Thu Jan 13 2005 John Dennis <jdennis@redhat.com> 0.99.13-2.devel
- make postgres & mysql conditional build
- remove execute bit on migration example scripts so rpm does not pull
  in additional dependences on perl and perl modules that are not present
  in dovecot proper.
- add REDHAT-FAQ.txt to doc directory

* Thu Jan  6 2005 John Dennis <jdennis@redhat.com> 0.99.13-1.devel
- bring up to date with latest upstream, 0.99.13, bug #143707
  also fix bug #14462, bad dovecot-uid macro name

* Thu Jan  6 2005 John Dennis <jdennis@redhat.com> 0.99.11-10.devel
- fix bug #133618, removed LITERAL+ capability from capability string

* Wed Jan  5 2005 John Dennis <jdennis@redhat.com> 0.99.11-9.devel
- fix bug #134325, stop dovecot during installation

* Wed Jan  5 2005 John Dennis <jdennis@redhat.com> 0.99.11-8.devel
- fix bug #129539, dovecot starts too early,
  set chkconfig to 65 35 to match cyrus-imapd
- also delete some old commented out code from SSL certificate creation

* Thu Dec 23 2004 John Dennis <jdennis@redhat.com> 0.99.11-7.devel
- add UW to Dovecot migration documentation and scripts, bug #139954
  fix SSL documentation and scripts, add missing documentation, bug #139276

* Thu Nov 15 2004 Warren Togami <wtogami@redhat.com> 0.99.11-2.FC4.1
- rebuild against MySQL4

* Thu Oct 21 2004 John Dennis <jdennis@redhat.com>
- fix bug #136623
  Change License field from GPL to LGPL to reflect actual license

* Thu Sep 30 2004 John Dennis <jdennis@redhat.com> 0.99.11-1.FC3.3
- fix bug #124786, listen to ipv6 as well as ipv4

* Wed Sep  8 2004 John Dennis <jdennis@redhat.com> 0.99.11-1.FC3.1
- bring up to latest upstream,
  comments from Timo Sirainen <tss at iki.fi> on release v0.99.11 2004-09-04  
  + 127.* and ::1 IP addresses are treated as secured with
    disable_plaintext_auth = yes
  + auth_debug setting for extra authentication debugging
  + Some documentation and error message updates
  + Create PID file in /var/run/dovecot/master.pid
  + home setting is now optional in static userdb
  + Added mail setting to static userdb
  - After APPENDing to selected mailbox Dovecot didn't always notice the
    new mail immediately which broke some clients
  - THREAD and SORT commands crashed with some mails
  - If APPENDed mail ended with CR character, Dovecot aborted the saving
  - Output streams sometimes sent data duplicated and lost part of it.
    This could have caused various strange problems, but looks like in
    practise it rarely caused real problems.

* Wed Aug  4 2004 John Dennis <jdennis@redhat.com>
- change release field separator from comma to dot, bump build number

* Mon Aug  2 2004 John Dennis <jdennis@redhat.com> 0.99.10.9-1,FC3,1
- bring up to date with latest upstream, fixes include:
- LDAP support compiles now with Solaris LDAP library
- IMAP BODY and BODYSTRUCTURE replies were wrong for MIME parts which
  didn't contain Content-Type header.
- MySQL and PostgreSQL auth didn't reconnect if connection was lost
  to SQL server
- Linking fixes for dovecot-auth with some systems
- Last fix for disconnecting client when downloading mail longer than
  30 seconds actually made it never disconnect client. Now it works
  properly: disconnect when client hasn't read _any_ data for 30
  seconds.
- MySQL compiling got broken in last release
- More PostgreSQL reconnection fixing


* Mon Jul 26 2004 John Dennis <jdennis@redhat.com> 0.99.10.7-1,FC3,1
- enable postgres and mySQL in build
- fix configure to look for mysql in alternate locations
- nuke configure script in tar file, recreate from configure.in using autoconf

- bring up to latest upstream, which included:
- Added outlook-pop3-no-nuls workaround to fix Outlook hang in mails with NULs.
- Config file lines can now contain quoted strings ("value ")
- If client didn't finish downloading a single mail in 30 seconds,
  Dovecot closed the connection. This was supposed to work so that
  if client hasn't read data at all in 30 seconds, it's disconnected.
- Maildir: LIST now doesn't skip symlinks


* Wed Jun 30 2004 John Dennis <jdennis@redhat.com>
- bump rev for build
- change rev for FC3 build

* Fri Jun 25 2004 John Dennis <jdennis@redhat.com> - 0.99.10.6-1
- bring up to date with upstream,
  recent change log comments from Timo Sirainen were:
  SHA1 password support using OpenSSL crypto library
  mail_extra_groups setting
  maildir_stat_dirs setting
  Added NAMESPACE capability and command
  Autocreate missing maildirs (instead of crashing)
  Fixed occational crash in maildir synchronization
  Fixed occational assertion crash in ioloop.c
  Fixed FreeBSD compiling issue
  Fixed issues with 64bit Solaris binary

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Thu May 27 2004 David Woodhouse <dwmw2@redhat.com> 0.99.10.5-1
- Update to 0.99.10.5 to fix maildir segfaults (#123022)

* Fri May 07 2004 Warren Togami <wtogami@redhat.com> 0.99.10.4-4
- default auth config that is actually usable
- Timo Sirainen (author) suggested functionality fixes
  maildir, imap-fetch-body-section, customflags-fix

* Mon Feb 23 2004 Tim Waugh <twaugh@redhat.com>
- Use ':' instead of '.' as separator for chown.

* Tue Feb 17 2004 Jeremy Katz <katzj@redhat.com> - 0.99.10.4-3
- restart properly if it dies (#115594)

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Nov 24 2003 Jeremy Katz <katzj@redhat.com> 0.99.10.4-1
- update to 0.99.10.4

* Mon Oct  6 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-7
- another patch from upstream to fix returning invalid data on partial 
  BODY[part] fetches
- patch to avoid confusion of draft/deleted in indexes

* Tue Sep 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-6
- add some patches from upstream (#104288)

* Thu Sep  4 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-5
- fix startup with 2.6 with patch from upstream (#103801)

* Tue Sep  2 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-4
- fix assert in search code (#103383)

* Tue Jul 22 2003 Nalin Dahyabhai <nalin@redhat.com> 0.99.10-3
- rebuild

* Thu Jul 17 2003 Bill Nottingham <notting@redhat.com> 0.99.10-2
- don't run by default

* Thu Jun 26 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-1
- 0.99.10

* Mon Jun 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-0.2
- 0.99.10-rc2 (includes ssl detection fix)
- a few tweaks from fedora
  - noreplace the config file
  - configure --with-ldap to get LDAP enabled

* Mon Jun 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-0.1
- 0.99.10-rc1
- add fix for ssl detection
- add zlib-devel to BuildRequires
- change pam service name to dovecot
- include pam config

* Thu May  8 2003 Jeremy Katz <katzj@redhat.com> 0.99.9.1-1
- update to 0.99.9.1
- add patch from upstream to fix potential bug when fetching with 
  CR+LF linefeeds
- tweak some things in the initscript and config file noticed by the 
  fedora folks

* Sun Mar 16 2003 Jeremy Katz <katzj@redhat.com> 0.99.8.1-2
- fix ssl dir
- own /var/run/dovecot/login with the correct perms
- fix chmod/chown in post

* Fri Mar 14 2003 Jeremy Katz <katzj@redhat.com> 0.99.8.1-1
- update to 0.99.8.1

* Tue Mar 11 2003 Jeremy Katz <katzj@redhat.com> 0.99.8-2
- add a patch to fix quoting problem from CVS

* Mon Mar 10 2003 Jeremy Katz <katzj@redhat.com> 0.99.8-1
- 0.99.8
- add some buildrequires
- fixup to build with openssl 0.9.7
- now includes a pop3 daemon (off by default)
- clean up description and %%preun
- add dovecot user (uid/gid of 97)
- add some buildrequires
- move the ssl cert to %%{_datadir}/ssl/certs
- create a dummy ssl cert in %%post
- own /var/run/dovecot
- make the config file a source so we get default mbox locks of fcntl

* Sun Dec  1 2002 Seth Vidal <skvidal@phy.duke.edu>
- 0.99.4 and fix startup so it starts imap-master not vsftpd :)

* Tue Nov 26 2002 Seth Vidal <skvidal@phy.duke.edu>
- first build
