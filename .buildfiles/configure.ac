#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
#AC_INIT(bpaddon, 0.9.7-alpha1, NagiosBP-Users@lists.nagiosforge.org)
AC_INIT(bp-addon, 0.9.7-alpha1, berny1@users.sourceforge.net)

dnl For later filesystem permissions
AC_DEFINE([DEFAULT_USER], [root], [Default User])
AC_DEFINE([DEFAULT_GROUP], [root], [Default Group])

AC_PREFIX_DEFAULT(/usr/local/bp-addon)

dnl Some information about the project
PKG_NAME=bp-addon
PKG_VERSION="0.9.7-alpha1"
PKG_HOME_URL="http://bp-addon.monitoringexchange.org/"
PKG_REL_DATE="14-11-2010"

AC_SUBST(PKG_NAME)
AC_SUBST(PKG_VERSION)
AC_SUBST(PKG_HOME_URL)
AC_SUBST(PKG_REL_DATE)


# Checks for programs.
AC_PROG_MAKE_SET
AC_PATH_PROG([STRIP],[strip],[true])

dnl maybe we need cp
AC_PATH_PROG(CP,cp)
AC_PATH_PROG(TOUCH,touch)

dnl Figure out how to invoke "install" and what install options to use.
AC_PROG_INSTALL
AC_SUBST(INSTALL)

dnl we definitely need perl
AC_PATH_PROG(PERL,perl)

# Checks for libraries.

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

# Checks for file permissions 

AC_ARG_WITH(bpaddon_user,[  --with-bpaddon-user=<user> sets the owner of installed files],bpaddon_user=$withval,bpaddon_user=root)
AC_ARG_WITH(bpaddon_group,[  --with-bpaddon-group=<grp> sets group of installed files],bpaddon_grp=$withval,bpaddon_grp=root)

AC_SUBST(bpaddon_user)
AC_SUBST(bpaddon_grp)

AC_DEFINE_UNQUOTED(DEFAULT_USER,"$bpaddon_user")
AC_DEFINE_UNQUOTED(DEFAULT_GROUP,"$bpaddon_grp")

INSTALL_OPTS="-o $bpaddon_user -g $bpaddon_grp"
AC_SUBST(INSTALL_OPTS)


#if test "$prefix" = "NONE" ;then
#	PRE="/usr/local/bp-addon"
#	LIB_DIR=$PRE/lib
#	CFG_DIR=$PRE/etc
#else
#	PRE=$prefix
#	LIB_DIR=$libdir
#	CFG_DIR=$sysconfdir
#fi

AC_ARG_WITH(cgiurl,[  --with-cgiurl=<local-url> sets URL for cgi programs],cgiurl=$withval,cgiurl=/bp-addon/cgi-bin)
AC_ARG_WITH(htmurl,[  --with-htmurl=<local-url> sets URL for public html],htmurl=$withval,htmurl=/bp-addon)
AC_SUBST(htmurl)
AC_SUBST(cgiurl)

dnl Check for location of Apache conf.d directory
HTTP_CONF=no
AC_ARG_WITH(httpd_conf,[  --with-httpd-conf=<path_to_conf> sets path to Apache conf.d directory],HTTPD_CONF=$withval,HTTPD_CONF=no)
if test x$HTTPD_CONF = xno; then
if test -d /etc/httpd/conf.d; then
	HTTPD_CONF="/etc/httpd/conf.d"
elif test -d /etc/apache2/conf.d; then
	HTTPD_CONF="/etc/apache2/conf.d"
elif test -d /etc/apache/conf.d; then
	HTTPD_CONF="/etc/apache/conf.d"
else
	HTTPD_CONF="$sysconfdir/apache-conf.d/"
fi
fi
AC_SUBST(HTTPD_CONF)

dnl Check for Apache user
apache_user=no
AC_ARG_WITH(apache_user,[  --with-apache-user=<user> sets path Apache runs with],apache_user=$withval,apache_user=no)
if test x$apache_user = xno; then
if grep -e "^apache:" /etc/passwd >/dev/null ; then
	# RedHat, Fedora, CentOS
	apache_user="apache"
elif grep -e "^www-data:" /etc/passwd >/dev/null ; then
	# Debian, Ubuntu, derivates of them
	apache_user="www-data"
elif grep -e "^wwwrun:" /etc/passwd >/dev/null ; then
	# SuSE
	apache_user="wwwrun"
else
	apache_user="root"
fi
fi
AC_SUBST(apache_user)

dnl Check for location of cron.d directory
CRON_D_DIR=no
AC_ARG_WITH(cron_d_dir,[  --with-cron-d-dir=<path_to_conf> sets path to cron.d directory],CRON_D_DIR=$withval,CRON_D_DIR=no)
if test x$CRON_D_DIR = xno; then
        if test -d /etc/cron.d; then
                CRON_D_DIR="/etc/cron.d"
        else
                CRON_D_DIR="$sysconfdir/cron.d/"
        fi
fi
AC_SUBST(CRON_D_DIR)

#AC_ARG_WITH(cgidir,[  --with-cgidir=/path/for/cgi-bin/ sets directory for cgi programs],cgidir=$withval,cgidir=/usr/local/bp-addon/sbin)
#AC_SUBST(cgidir)

#langdir=no
#AC_ARG_WITH(langdir,[  --with-langdir=/path/for/lang/ sets directory for language files],langdir=$withval,langdir=no)
#if test x$langdir = xno; then
#	echo langdir $langdir
#	echo exec_prefix ${exec_prefix}
#	langdir=${exec_prefix}/lang
#fi
#AC_SUBST(langdir)

AC_ARG_WITH(nagetc,[  --with-nagetc=/path/to/nagios/etc sets path to Nagios or Icinga etc directory],nagetc=$withval,nagetc=/usr/local/nagios/etc)
AC_SUBST(nagetc)

AC_ARG_WITH(naghtmurl,[  --with-naghtmurl=<local-url> sets URL for Nagios or Icinga HTM URL],naghtmurl=$withval,naghtmurl=/nagios)
AC_SUBST(naghtmurl)

AC_ARG_WITH(nagcgiurl,[  --with-nagcgiurl=<local-url> sets URL for Nagios or Icinga cgi programs],nagcgiurl=$withval,nagcgiurl=/nagios/cgi-bin)
AC_SUBST(nagcgiurl)

dnl AuthName directive in apache config
apache_authname="Nagios Access"
AC_ARG_WITH(apache_authname,[  --with-apache-authname=<authname> sets value of AuthName directive in Apache config],apache_authname=$withval,apache_authname="Nagios Access")
if test $(echo $naghtmurl | grep -i icinga | wc -l) -gt 0 -a "x$apache_authname" = "xNagios Access"; then
	apache_authname="Icinga Access"
fi
AC_SUBST(apache_authname)

AC_SUBST(LIB_DIR)
AC_SUBST(CFG_DIR)

AC_CONFIG_FILES(
	subst
	Makefile
	bin/Makefile 
	sbin/Makefile
	etc/Makefile 
	etc/apache-conf.d/Makefile 
	etc/cron.d/Makefile 
	lib/Makefile 
	libexec/Makefile 
	var/bp-addon.sessions/Makefile
	var/cache/Makefile
	share/Makefile
	share/stylesheets/Makefile
	share/lang/Makefile)

AC_OUTPUT

$PERL subst sbin/bp-addon.cgi
$PERL subst sbin/whereUsed.cgi
$PERL subst lib/businessProcessFunctions.pm
$PERL subst lib/dataBackend.pm
$PERL subst lib/bsutils.pm
$PERL subst lib/settings.pm
$PERL subst libexec/check_bp_status.pl
$PERL subst bin/bp-cfg2service-cfg.pl
$PERL subst bin/bp-addon-consistency-check.pl
$PERL subst bin/bp-addon-check-backend-connection.pl
$PERL subst bin/bp-addon-session-timeout
$PERL subst etc/settings.cfg
$PERL subst etc/dataBackend.cfg-sample
$PERL subst etc/apache-conf.d/bp-addon.conf
$PERL subst etc/cron.d/bp-addon

dnl Review options
echo ""
echo ""
AC_MSG_RESULT([*** Configuration summary for $PKG_NAME $PKG_VERSION $PKG_REL_DATE ***:])

echo ""
echo " General Options:"
echo " -------------------------"

AC_MSG_RESULT([       Install user/group:  $bpaddon_user,$bpaddon_grp])
AC_MSG_RESULT([        Install \${prefix}:  $prefix])
AC_MSG_RESULT([   Install \${exec_prefix}:  $exec_prefix])
AC_MSG_RESULT([                  LIB Dir:  $libdir])
AC_MSG_RESULT([               Config Dir:  $sysconfdir])
#AC_MSG_RESULT([                Share Dir:  $datarootdir])
AC_MSG_RESULT([                 Data Dir:  $datadir])
#AC_MSG_RESULT([             Language Dir:  $langdir])
#AC_MSG_RESULT([                  CGI Dir:  $cgidir])
AC_MSG_RESULT([                  HTM URL:  $htmurl])
AC_MSG_RESULT([                  CGI URL:  $cgiurl])
AC_MSG_RESULT([        Nagios Config Dir:  $nagetc])
AC_MSG_RESULT([           Nagios HTM URL:  $naghtmurl])
AC_MSG_RESULT([           Nagios CGI URL:  $nagcgiurl])
AC_MSG_RESULT([        Apache conf.d Dir:  $HTTPD_CONF])
AC_MSG_RESULT([              Apache User:  $apache_user])
AC_MSG_RESULT([          Apache AuthName:  $apache_authname])
AC_MSG_RESULT([               cron.d Dir:  $CRON_D_DIR])
echo ""
echo ""
echo "Review the options above for accuracy.  If they look okay,"
echo "type 'make install' to install."
echo ""
