# The docs have to prebuild.
#
# Instructions for rebasing:
# - Change the Version tag, and replace the old version with the new in the
#   commands in this list of instructions.
# - Get the sources and remove exe files (more info later in the spec file)
#   $ ./get-source.sh 2.7.16
# - Touch the pre-built source file, so that the build doesn't exit prematurely
#   $ touch built-python2-docs-2.7.16.tar.gz
# - Do a pre-build — the `prebuilt` bcond is set by a flag! Update the Fedora
#   version here and in the next step if needed.
#   $ fedpkg --release f29 mockbuild -N --without prebuilt --root fedora-29-x86_64
# - Get the built docs and tar them up for the next build (update fedora
#   version if needed)
#   $ pushd /var/lib/mock/fedora-29-x86_64/root/builddir/build/BUILD/Python-2.7.16/
#   $ tar -zcvf built-python2-docs-2.7.16.tar.gz Doc/build/texinfo/python.info Doc/build/html
#   $ popd
#   $ cp /var/lib/mock/fedora-29-x86_64/root/builddir/build/BUILD/Python-2.7.16/built-python2-docs-2.7.16.tar.gz .
# - Add the new Python source and the pre-built docs into distgit and commit!
#   $ rhpkg new-sources built-python2-docs-2.7.16.tar.gz Python-2.7.16-noexe.tar.xz


# Reasoning:
# It is impossible to build the python2-docs in the python27 module because:
# - python2-sphinx is not available for RHEL => we have to use python3-sphinx
# - due to issue with MBS, python2 components that are built in the python27
#   module overshadow their python3 counterparts, and therefore we cannot use
#   python3-sphinx as some of its python3 dependencies are not found
# Therefore we prebuild it in a Fedora mock. We could also prebuild it in a
# RHEL8 mock, but there's no `linkchecker` package in RHEL8, so the tests cannot
# be run.
%bcond_without prebuilt

# The linkchecker executable isn't available in RHEL8, so enable only when
# prebuilding on Fedora. Check is only done when the sources are being prebuilt.
%bcond_without check_links

%define pybasever 2.7

Name:			python-docs
# The Version needs to be in-sync with the "python2" package:
Version:		2.7.16
Release:		2%{?dist}
Summary:		Documentation for the Python 2 programming language
Group:			Documentation
License:		Python
URL:			https://www.python.org/

# The upstream tarball includes questionable executable files for Windows,
# which we should not ship even in the SRPM.
# Run the "get-source.sh" with the version as argument to download the upstream
# tarball and generate a version with the .exe files removed. For example:
# $ ./get-source.sh 3.7.0
#   (if there's a newer version of this script in the python3 component, update
#   it here)
Source: Python-%{version}-noexe.tar.xz

# A script to remove .exe files from the source distribution
# The authoritative version of this script is in the python3 component, if it's
# updated there, copy the new version here as well
Source1: get-source.sh

# See the top of this spec file (bcond `prebuilt`) for details
Source2: built-python2-docs-%{version}.tar.gz

# this changes the makefile so that build requires are used instead of
# hard coded svn checkout to get sphinx
Patch19: python-2.7-texinfomakefile.patch
# this enables the texinfo builder
Patch20: python-2.7-texinfobuilder.patch

BuildArch:		noarch

%if %{without prebuilt}
BuildRequires:	python3
BuildRequires:	python3-docutils
BuildRequires:	python3-pygments
BuildRequires:	python3-sphinx
BuildRequires:	linkchecker
BuildRequires:	texinfo
%endif


%description
The python2-docs package contains documentation on the Python 2
programming language and interpreter.

Install the python2-docs package if you'd like to use the documentation
for the Python 2 language.


%package -n python2-docs
Summary:		%{summary}
Recommends:		python2 = %{version}

%description -n python2-docs
The python2-docs package contains documentation on the Python 2
programming language and interpreter.

Install the python2-docs package if you'd like to use the documentation
for the Python 2 language.


%package -n python2-docs-info
Summary:		Documentation for the Python 2 programming language as info pages
Group:			Documentation
Requires(post):	info
Requires(preun):info

%description -n python2-docs-info
The python2-docs-info package contains documentation on the Python 2
programming language and interpreter as info pages.

Install the python2-docs-info package if you'd like to read the
documentation for the Python 2 language using the info command or Emacs.


%prep
%setup -q -n Python-%{version}

%patch19 -p1 -b .texinfomakefile
%patch20 -p1 -b .texinfobuilder


%build
%if %{with prebuilt}

# Unpack the prebuilt html and info files to their original locations
tar -zxvf %{SOURCE2}

%else # without prebuilt

make -C Doc html

# build info docs
make -C Doc texinfo
make -C Doc/build/texinfo info

# Remove the sphinx-build leftovers
rm -fr Doc/build/html/.{doctrees,buildinfo}

# Work around rhbz#670493:
ln -s ./py-modindex.html Doc/build/html/modindex.html

%endif # without prebuilt


%install
# install info files
mkdir -p %{buildroot}%{_infodir}
cp -v Doc/build/texinfo/python.info %{buildroot}%{_infodir}/python2.info

# edit path to image file in info page
sed -i -e 's,logging_flow\.png,%{_pkgdocdir}/html/_images/&,' \
    %{buildroot}%{_infodir}/python2.info


%post -n python2-docs-info
/sbin/install-info %{_infodir}/python2.info %{_infodir}/dir || :

%preun -n python2-docs-info
if [ $1 = 0 ]; then
/sbin/install-info --delete %{_infodir}/python2.info.gz %{_infodir}/dir || :
fi


%check
#    NOTICE:
#        The check has been disabled when doing the actual build because
#        linkchecker isn't available on RHEL8, however we can still do the
#        check when we're prebuilding the docs on Fedora
#
# Verify that all of the local links work (see rhbz#670493)
#
# (we can't check network links, as we shouldn't be making network connections
# within a build.  Also, don't bother checking the .txt source files; some
# contain example URLs, which don't work)
%if %{without prebuilt}
%if %{with check_links}
linkchecker \
  --ignore-url=^mailto: --ignore-url=^http --ignore-url=^ftp \
  --ignore-url=.txt\$ --no-warnings \
  Doc/build/html/index.html
%endif # with check_links
%endif # without prebuilt


%files -n python2-docs
%doc		Misc/NEWS  Misc/README Misc/cheatsheet
%doc		Misc/HISTORY Doc/build/html
%license	LICENSE

%files -n python2-docs-info
%{_infodir}/python2.info.gz
%license	LICENSE


%changelog
* Thu Apr 25 2019 Tomas Orsava <torsava@redhat.com> - 2.7.16-2
- Bumping due to problems with modular RPM upgrade path
- Resolves: rhbz#1695587

* Wed Mar 27 2019 Tomas Orsava <torsava@redhat.com> - 2.7.16-1
- Update to 2.7.16
Resolves: rhbz#1680967

* Thu Dec 13 2018 Tomas Orsava <torsava@redhat.com> - 2.7.15-3
- Modify for prebuilding and deploying on RHEL8
- Rename the info page to python2
- Resolves: rhbz#1656048

* Wed Dec 05 2018 Tomas Orsava <torsava@redhat.com> - 2.7.15-2
- Modify for building on RHEL8
- Disable the tests, because the linkchecker package isn't available in RHEL8
- Resolves: rhbz#1656048

* Sat May 12 2018 Miro Hrončok <mhroncok@redhat.com> - 2.7.15-1
- Update to 2.7.15

* Thu Apr 19 2018 Miro Hrončok <mhroncok@redhat.com> - 2.7.14-5
- Only recommend the python2 package

* Fri Apr 13 2018 Miro Hrončok <mhroncok@redhat.com> - 2.7.14-4
- Remove Obsoletes tag from when python was renamed to python2 (Fedora 25 was last)

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.14-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Mon Dec 04 2017 Iryna Shcherbina <ishcherb@redhat.com> - 2.7.14-2
- Fix ambiguous Python 2 dependencies declarations
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Thu Nov 02 2017 Charalampos Stratakis <cstratak@redhat.com> - 2.7.14-1
- Update to 2.7.14

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.13-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jun 01 2017 Miro Hrončok <mhroncok@redhat.com> - 2.7.13-3
- Change fixed Obsoletes version with a dynamic one (rhbz#1457336)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Jan 11 2017 Charalampos Stratakis <cstratak@redhat.com> - 2.7.13-1
- Update to 2.7.13
- Rename package to python2-docs

* Mon Sep 05 2016 Charalampos Stratakis <cstratak@redhat.com> - 2.7.12-2
- Remove unversioned Obsoletes.

* Wed Jul 20 2016 Jon Ciesla <limburgher@gmail.com> - 2.7.12-1
- Update to 2.7.12.

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Dec 24 2015 Robet Kuska <rkuska@redhat.com> - 2.7.11-1
- Update to 2.7.11

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed May 27 2015 Matej Stuchlik <mstuchli@redhat.com> - 2.7.10-1
- Update to 2.7.10

* Fri Dec 12 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.7.9-1
- Update to 2.7.9

* Fri Aug 01 2014 Robert Kuska <rkuska@redhat.com> - 2.7.8-1
- Update to 2.7.8

* Tue Jun 10 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.7.7-1
- Update to 2.7.7

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Feb 05 2014 Tomas Radej <tradej@redhat.com> - 2.7.6-1
- Updated to v2.7.6

* Mon Dec 02 2013 Tomas Radej <tradej@redhat.com> - 2.7.5-6
- Used _pkgdocdir instead of _docdir

* Tue Nov 26 2013 Tomas Radej <tradej@redhat.com> - 2.7.5-5
- Small tweaks of Suvayu's patch

* Sun Nov 24 2013 Suvayu Ali <fatkasuvayu+linux@gmail.com> - 2.7.5-4
- Enable Texinfo builder, add subpackage with python info pages

* Fri Nov 22 2013 Tomas Radej <tradej@redhat.com> - 2.7.5-3
- Spec cleanup

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri May 24 2013 Bohuslav Kabrda <bkabrda@redhat.com> - 2.7.5-1
- Version 2.7.5.

* Thu Apr 11 2013 Bohuslav Kabrda <bkabrda@redhat.com> - 2.7.4-1
- Version 2.7.4.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed May 23 2012 David Malcolm <dmalcolm@redhat.com> - 2.7.3-2
- make link checking optional, to avoid needing to pull in linkchecker and
its dependencies (rbhz#823930)

* Fri Apr 13 2012 David Malcolm <dmalcolm@redhat.com> - 2.7.3-1
- 2.7.3

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Aug 11 2011 David Malcolm <dmalcolm@redhat.com> - 2.7.2-2
- fix broken link to "Global Module Index", and add a %%check, verifying the
absence of broken links (rhbz#670493)

* Wed Jun 22 2011 David Malcolm <dmalcolm@redhat.com> - 2.7.2-1
- 2.7.2

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec 30 2010 David Malcolm <dmalcolm@redhat.com> - 2.7.1-1
- 2.7.1

* Mon Aug 02 2010 Roman Rakus <rrakus@redhat.com> - 2.7-1
- Update to 2.7

* Sat Mar 20 2010 David Malcolm <dmalcolm@redhat.com> - 2.6.5-1
- move to 2.6.5: http://www.python.org/download/releases/2.6.5/

* Fri Jan 29 2010 David Malcolm <dmalcolm@redhat.com> - 2.6.4-3
- fix %%description (bug #559710)

* Fri Oct 30 2009 David Malcolm <dmalcolm@redhat.com> - 2.6.4-2
- update sources for 2.6.4

* Fri Oct 30 2009 David Malcolm <dmalcolm@redhat.com> - 2.6.4-1
- move to 2.6.4
- drop build requirement on python-jinja; python-sphinx requires python-jinja2
(bug 532135)

* Fri Jul 31 2009 Jame Antill <james.antill@redhat.com> - 2.6.2-1
- Move to 2.6.2 like python itself.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jul 22 2009 Roman Rakus <rrakus@redhat.com> - 2.6-4
- Fix import error (#511647)

* Wed May 06 2009 Roman Rakus <rrakus@redhat.com> - 2.6-3
- Spec file cleanup (#226341)

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 2.6-1
- Update to 2.6

* Wed Oct  1 2008 Jame Antill <james.antill@redhat.com> - 2.5.2-1
- Move to 2.5.2 like python itself.

* Wed Sep  3 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 2.5.1-3
- fix license tag

* Mon Feb 11 2008 Jame Antill <james.antill@redhat.com> - 2.5.1-2
- mkdir a build root to keep recent rpm/mock happy.

* Sun Jun 03 2007 Florian La Roche <laroche@redhat.com> - 2.5.1-1
- update to 2.5.1

* Tue Dec 12 2006 Jeremy Katz <katzj@redhat.com> - 2.5-1
- update to 2.5

* Tue Oct 24 2006 Jeremy Katz <katzj@redhat.com> - 2.4.4-1
- update to 2.4.4

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 2.4.3-1.1
- rebuild

* Sat Apr  8 2006 Mihai Ibanescu <misa@redhat.com> 2.4.3-1
- updated to 2.4.3

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Wed Nov 16 2005 Mihai Ibanescu <misa@redhat.com> 2.4.2-1
- updated to 2.4.2

* Fri Apr  8 2005 Mihai Ibanescu <misa@redhat.com> 2.4.1-1
- updated to 2.4.1

* Thu Mar 17 2005 Mihai Ibanescu <misa@redhat.com> 2.4-102
- changed package to noarch

* Mon Mar 14 2005 Mihai Ibanescu <misa@redhat.com> 2.4-100
- split the doc building step into a separate source rpm
