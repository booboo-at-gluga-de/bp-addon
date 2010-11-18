#!/bin/bash

#    Business Process AddOns for Nagios and Icinga
#    Copyright (C) 2003-2010 Sparda-Datenverarbeitung eG, Nuernberg, Germany
#    Bernd Stroessreuther <berny1@users.sourceforge.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


BUILDFILES_SRCDIR=/usr/local/bp-addon/.buildfiles/
SOURCEFILES_DIR=/usr/local/bp-addon/
BUIDLROOT=/usr/local/bp-addon-buildroot/
CONFIGURE_AC=$BUILDFILES_SRCDIR/configure.ac

if [ `whoami` != "root" ]
then
	echo should be run as root
	echo aborting...
	exit 1
fi

if [ -z $1 ]
then
	echo
	echo Make sure, the values You did set in $CONFIGURE_AC are actual
	echo especially watch out for these:
	echo
	grep AC_INIT $CONFIGURE_AC
	egrep "^PKG_" $CONFIGURE_AC
	echo
	perl -e 'use lib("/usr/local/bp-addon/lib"); use settings; print "Version according to settings.pm: " . getVersion() . "\n"'
	echo
	echo -n "Are they? "
	read ANSWER
	if [ "$ANSWER" = "y" -o "$ANSWER" = "yes" -o "$ANSWER" = "Y" -o "$ANSWER" = "YES" ]
	then
		echo fine!
	else
		echo aborting...
		exit 1
	fi

	echo -n "Build: (0 for final) "
	read BUILD
else
	echo
	echo Building with the following values from $CONFIGURE_AC:
	echo
	grep AC_INIT $CONFIGURE_AC
	egrep "^PKG_" $CONFIGURE_AC
	echo
	BUILD=$1
	echo Build $BUILD
	echo
fi

echo
echo checking base files
echo -------------------
. $SOURCEFILES_DIR/etc/dataBackend.cfg
if [ "$cache_time" -ne 0 ]
then
	echo in $SOURCEFILES_DIR/etc/dataBackend.cfg cache_time=$cache_time, should be 0
	exit 1
fi
if [ "$backend" != "db" ]
then
	echo in $SOURCEFILES_DIR/etc/dataBackend.cfg backend=$ndo, should be db
	exit 1
fi

if [ "$BUILD" != "0" ]
then
	BUILDSTRING=".build$BUILD"
fi

eval `egrep "^PKG_VERSION" $CONFIGURE_AC`
VERSION_IN_SETTINGS_PM=`perl -e "use lib ('/usr/local/bp-addon/lib/'); use settings; print getVersion() . \"\n\";"`
echo Version number according to $SOURCEFILES_DIR/lib/settings.pm is $VERSION_IN_SETTINGS_PM

if [ "$VERSION_IN_SETTINGS_PM" != "$PKG_VERSION" ]
then
	echo does not match version in $CONFIGURE_AC: $PKG_VERSION
	exit 1
fi

/usr/local/validate.user.css.pl /usr/local/bp-addon/share/stylesheets/user.css || exit 1

VERSIONSTRING="business-process-addon-$PKG_VERSION$BUILDSTRING"
FILE="/usr/local/$VERSIONSTRING.tar.gz"
echo building $FILE
rm -Rf $BUIDLROOT/*
cd /usr/local || exit 1
mkdir $BUIDLROOT/$VERSIONSTRING || exit 1
rm -f $SOURCEFILES_DIR/var/bp-addon.sessions/*
cp -R $SOURCEFILES_DIR/* $BUIDLROOT/$VERSIONSTRING
cp -R $BUILDFILES_SRCDIR/* $BUIDLROOT/$VERSIONSTRING
mv $BUIDLROOT/$VERSIONSTRING/etc/business-processes.conf $BUIDLROOT/$VERSIONSTRING/etc/business-processes.conf-sample
mv $BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg $BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg-sample
rm -f $BUIDLROOT/$VERSIONSTRING/etc/business-processes-second-view.conf
#rm -f $BUIDLROOT/$VERSIONSTRING/share/stylesheets/user.css
rm -f $BUIDLROOT/$VERSIONSTRING/var/bp-addon.sessions/.gitignore
rm -f $BUIDLROOT/$VERSIONSTRING/var/bp-addon.sessions/.placeholder
rm -f $BUIDLROOT/$VERSIONSTRING/build-bp-addon.sh
rm -f $BUIDLROOT/$VERSIONSTRING/var/cache/.placeholder

cd $BUIDLROOT/$VERSIONSTRING || exit 1
autoconf
rm -Rf $BUIDLROOT/$VERSIONSTRING/autom4te.cache
echo
echo string replacement in the following files...
echo --------------------------------------------
for INFILE in `find $BUIDLROOT -type f -and \( -name "*.pl" -or -name "bp-addon-session-timeout" -or -name "*.pm" -or -name "settings.cfg" -or -name "dataBackend.cfg-sample" -or -name "*.cgi" \)`
do
	echo $INFILE
	cat $INFILE | sed -e "s#/usr/local/bp-addon/lib/#@libdir@#" -e "s#/usr/local/bp-addon/etc#@sysconfdir@#" -e "s#/usr/bin/perl#@PERL@#" -e "s#/usr/local/bp-addon/var#@localstatedir@#" >${INFILE}.in
	rm -f $INFILE
done

echo
echo special string replacement in single files
echo ------------------------------------------
echo settings.cfg
cat $BUIDLROOT/$VERSIONSTRING/etc/settings.cfg.in | sed \
-e "s#/usr/local/bp-addon/bin#@bindir@#" \
-e "s#/usr/local/bp-addon/libexec#@libexecdir@#" \
-e "s#/usr/local/bp-addon/lib#@libdir@#" \
-e "s#/usr/local/bp-addon/sbin#@sbindir@#" \
-e "s#/usr/local/bp-addon/share#@datarootdir@#" \
-e "s#/usr/local/bp-addon/lang#@langdir@#" \
-e "s#BP_ADDON_HTML_URL=/bp-addon#BP_ADDON_HTML_URL=@htmurl@#" \
-e "s#BP_ADDON_CGI_URL=/bp-addon/cgi-bin#BP_ADDON_CGI_URL=@cgiurl@#" \
-e "s#NAGIOS_ETC=/usr/local/nagios/etc#NAGIOS_ETC=@nagetc@#" \
-e "s#NAGIOS_BASE_URL=/nagios#NAGIOS_BASE_URL=@naghtmurl@#" \
-e "s#NAGIOS_CGI_URL=/nagios/cgi-bin#NAGIOS_CGI_URL=@nagcgiurl@#" >$BUIDLROOT/$VERSIONSTRING/etc/settings.cfg.in.tmp
mv $BUIDLROOT/$VERSIONSTRING/etc/settings.cfg.in.tmp $BUIDLROOT/$VERSIONSTRING/etc/settings.cfg.in
echo dataBackend.cfg
cat $BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg-sample.in | sed \
-e "s+ndodb_prefix=ndo_+#ndodb_prefix=ndo_+" \
-e "s+#ndodb_prefix=nagios_+ndodb_prefix=nagios_+" >$BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg-sample.in.tmp
mv $BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg-sample.in.tmp $BUIDLROOT/$VERSIONSTRING/etc/dataBackend.cfg-sample.in
echo cleaning backend_cache
echo -n > $BUIDLROOT/$VERSIONSTRING/var/cache/backend_cache

echo
echo checking for errors
echo -------------------
find $BUIDLROOT -type f ! -name UPDATE ! -name `basename $0` -exec grep -H nagios-ext {} \;

chown -R root.root $BUIDLROOT
chmod -R g-w,o+rX $BUIDLROOT
chmod 1777  $BUIDLROOT/$VERSIONSTRING/var/bp-addon.sessions
cd $BUIDLROOT || exit 1
echo
echo tar the result-file
echo -------------------
tar cvzf $FILE $VERSIONSTRING || exit 1
echo
echo OK
echo
