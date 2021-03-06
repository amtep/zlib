Name:       zlib

%define binutils_ver %(rpm -q --queryformat='%%{version}' binutils | awk -F. '{print $1$2}')
%define keepstatic 1

Summary:    The zlib compression and decompression library
Version:    1.2.8
Release:    1
Group:      System/Libraries
License:    zlib and Boost
URL:        http://www.gzip.org/zlib/
Source0:    http://www.zlib.net/%{name}-%{version}.tar.gz
Source100:  zlib.yaml
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
BuildRequires:  automake
BuildRequires:  autoconf
BuildRequires:  libtool

%description
Zlib is a general-purpose, patent-free, lossless data compression
library which is used by many different programs.


%package static
Summary:    Static libraries for Zlib development
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}

%description static
The zlib-static package includes static libraries needed
to develop programs that use the zlib compression and
decompression library.


%package -n minizip
Summary:    Minizip manipulates files from a .zip archive
Group:      System/Libraries
Requires:   %{name} = %{version}-%{release}
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n minizip
Minizip manipulates files from a .zip archive.

%package -n minizip-devel
Summary:    Development files for the minizip library
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}

%description -n minizip-devel
This package contains the libraries and header files needed for
developing applications which use minizip.


%package devel
Summary:    Header files and libraries for Zlib development
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}

%description devel
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.


%prep
%setup -q -n %{name}-%{version}/%{name}

mkdir contrib/minizip/m4

%build
%ifarch  %{arm}
export CFLAGS="$RPM_OPT_FLAGS -mfpu=neon"
%else
export CFLAGS="$RPM_OPT_FLAGS"
%endif

./configure --libdir=%{_libdir} --includedir=%{_includedir} --prefix=%{_prefix}

#ensure 64 offset versions are compiled (do not override CFLAGS blindly)
export CFLAGS="`grep -E ^CFLAGS Makefile | sed -e 's/CFLAGS=//'`"
export SFLAGS="`grep -E ^SFLAGS Makefile | sed -e 's/SFLAGS=//'`"

#
# first,build with -fprofile-generate to create the profile data
#
make %{?_smp_mflags} CFLAGS="$CFLAGS -pg -fprofile-generate" SFLAGS="$SFLAGS -pg -fprofile-generate"

#
# Then run some basic operations using the minigzip test program
# to collect the profile guided stats
# (in this case, we compress and decompress the content of /usr/bin)
#
cp Makefile Makefile.old
make test -f Makefile.old LDFLAGS="libz.a -lgcov"
cat /usr/bin/* | ./minigzip | ./minigzip -d &> /dev/null

#
# Now that we have the stats, we need to build again, using -fprofile-use
# Due to the libtool funnies, we need to hand copy the profile data to .libs
#
mkdir libs-tmp
cp *gcda libs-tmp
make clean
mv libs-tmp/*gcda .
rm -rf libs-tmp

#
# Final build, with -fprofile-use
#

%ifarch %{ix86} x86_64
make %{?_smp_mflags} CFLAGS="$CFLAGS -DHAVE_BINUTILS=%{binutils_ver}"  SFLAGS="$SFLAGS " adler32.o adler32.lo
%endif
make %{?_smp_mflags} CFLAGS="$CFLAGS -fprofile-use -DHAVE_BINUTILS=%{binutils_ver}"  SFLAGS="$SFLAGS -fprofile-use"
cd contrib/minizip
%reconfigure --disable-static
export CFLAGS="$RPM_OPT_FLAGS -DHAVE_BINUTILS=%{binutils_ver}"
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
%make_install

cd contrib/minizip
make install DESTDIR=$RPM_BUILD_ROOT

rm $RPM_BUILD_ROOT%{_libdir}/*.la

%check
make test

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%post -n minizip -p /sbin/ldconfig

%postun -n minizip -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%{_libdir}/libz.so.*

%files static
%defattr(-,root,root,-)
%doc README
%{_libdir}/libz.a

%files -n minizip
%defattr(-,root,root,-)
%doc contrib/minizip/MiniZip64_info.txt contrib/minizip/MiniZip64_Changes.txt
%{_libdir}/libminizip.so.*

%files -n minizip-devel
%defattr(-,root,root,-)
%dir %{_includedir}/minizip
%{_includedir}/minizip/*.h
%{_libdir}/libminizip.so
%{_libdir}/pkgconfig/minizip.pc

%files devel
%defattr(-,root,root,-)
%doc README doc/algorithm.txt test/example.c ChangeLog FAQ
%{_libdir}/libz.so
%{_includedir}/zconf.h
%{_includedir}/zlib.h
%{_mandir}/man3/zlib.3*
%{_libdir}/pkgconfig/zlib.pc
