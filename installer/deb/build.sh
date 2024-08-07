#!/bin/bash
set -e

# cd to working dir
cd "$(dirname "$0")"


# build client .deb package
INSTALLDIR=/usr/share/SerialCommander
BUILDDIR=serialcommander

# empty / create necessary directories
if [ -d "$BUILDDIR/usr" ]; then
	rm -r $BUILDDIR/usr
fi

# copy files in place
install -D -m 644 ../../README.md                       -t $BUILDDIR/$INSTALLDIR
install -D -m 755 ../../SerialCommander.py              -t $BUILDDIR/$INSTALLDIR
install -D -m 644 ../../examples/*                      -t $BUILDDIR/$INSTALLDIR/examples
install -D -m 644 ../../assets/icon.svg                 -t $BUILDDIR/usr/share/pixmaps/SerialCommander
install -D -m 644 ../../assets/SerialCommander.desktop  -t $BUILDDIR/usr/share/applications
install -D -m 644 ../../assets/SerialCommander-Autostart.desktop  -t $BUILDDIR/etc/xdg/autostart

# make binaries available in PATH
mkdir -p $BUILDDIR/usr/bin
ln -sf   $INSTALLDIR/SerialCommander.py     $BUILDDIR/usr/bin/serialcommander


# build debs
dpkg-deb -Zxz --root-owner-group --build serialcommander

echo "Build finished"
