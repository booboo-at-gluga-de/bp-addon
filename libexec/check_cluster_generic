#!/usr/bin/perl

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


# replacement for check_cluster
# which can work with nagios/icinga no matter if we use NDO/IDO/Merlin/mk_livestatus
# or whatever backend as long as business process Addon is installed
#
# 2010-12-21

use strict;
use lib ('/usr/local/bp-addon/lib/');
use dataBackend;

my ($cmd, $in, $param, $value, $i, $type, $clusterDefFile, $warningThresh, $criticalThresh, @clustermembers, $undefMembers, $hardstates, $statusinfos, $key, $member);
my $rc = 3;
my $okCount = 0;
my $nonOkCount = 0;
my $debug = 0;
my $help = 0;
my $version = 0;
my %rcstring = ( 0 => "OK", 1 => "WARNING", 2 => "CRITICAL", 3 => "UNKNOWN", -1 => "UNKNOWN");

# get the command line parameters
for ($i=0; $i<@ARGV; $i++)
{
	if ($ARGV[$i] eq "--service")
	{
		$type = "service";
	}
	elsif ($ARGV[$i] eq "--host")
	{
		$type = "host";
	}
	elsif ($ARGV[$i] eq "-d")
	{
		$debug = 1;
	}
	elsif ($ARGV[$i] eq "-f")
	{
		$i++;
		$clusterDefFile = $ARGV[$i];
	}
	elsif ($ARGV[$i] eq "-w")
	{
		$i++;
		$warningThresh = $ARGV[$i];
	}
	elsif ($ARGV[$i] eq "-c")
	{
		$i++;
		$criticalThresh = $ARGV[$i];
	}
	elsif ($ARGV[$i] eq "-h" || $ARGV[$i] eq "--help")
	{
		$help = 1;
	}
	elsif ($ARGV[$i] eq "-V" || $ARGV[$i] eq "--version")
	{
		$version = 1;
	}
}

# display version or help if needed
if ($version == 1)
{
	use settings;
	print "Version " . getVersion() . "\n";
	exit(0);
}
if ($help == 1)
{
	help();
	exit(0);
}
if ($type !~ m/^(host|service)$/ || $clusterDefFile eq "" || $warningThresh !~ m/^\d+$/ || $criticalThresh !~ m/^\d+$/)
{
	print "Could not parse arguments\n\n";
	help();
	exit(3);
}

#read the cluster definition file
open(IN, "<$clusterDefFile") or die "unable to read $clusterDefFile: $!\n"; 
	while ($in = <IN>)
	{
		#print "$in";
		chomp($in);
		push (@clustermembers, $in);
	}
close(IN);


#read the status data for all clustermembers 
($hardstates, $statusinfos) = &getStates();
#foreach $key (keys %$hardstates)
#{
#	print "DEBUG: $key $hardstates->{$key}\n";
#}

foreach $i (@clustermembers)
{
	# print "DEBUG: $i\n";

	$member = $i;	
	if ($type eq "host")
	{
		$member .= ";Hoststatus";
	}

	print STDERR "DEBUG: Status for $type \"$i\" is \"$hardstates->{$member}\"\n" if ($debug > 0);

	if ($hardstates->{$member} eq "OK")
	{
		$okCount++;
	}
	else
	{
		$nonOkCount++;
	}
}

#print scalar @clustermembers . " clustermembers\n";
#print "$okCount okCount\n";
#print "$nonOkCount nonOkCount\n";
$undefMembers = scalar @clustermembers - $okCount - $nonOkCount;
if ($undefMembers > 0)
{
	print "UNKNOWN: $undefMembers $type(s) defined in $clusterDefFile cannot be found in Nagios/Icinga\n";
	exit(3);
}

if ($nonOkCount < $warningThresh) { $rc = 0 }
if ($nonOkCount >= $warningThresh) { $rc = 1 }
if ($nonOkCount >= $criticalThresh) { $rc = 2 }
if ($nonOkCount == 0 && $okCount == 0) { $rc = 3 }

if ($type eq "service")
{
	print "ServiceCluster is $rcstring{$rc}: $okCount in OK state, $nonOkCount in not OK state\n";
}
else
{
	print "HostCluster is $rcstring{$rc}: $okCount UP, $nonOkCount DOWN\n";
}
exit($rc);


sub help()
{
	print "Usage: $0 --service|--host -f <clusterDefFile> -w <warn_threshold> -c <crit_threshold> [-d]\n";
	print "or:    $0 --help|-h\n";
	print "or:    $0 --version|-V\n\n";
	print "--service        Check service cluster status\n";
	print "--host           Check host cluster status\n";
	print "<clusterDefFile> Definition file for the cluster\n";
	print "                 One host or service can be specified per line, services must\n";
	print "                 be in the format of <host_name>;<svc_description>\n";
	print "<warn_threshold> This is the number of hosts or services in\n";
	print "                 the cluster that must be in a non-OK state\n";
	print "                 in order to result in a warning status level\n";
	print "<crit_threshold> This is the number of hosts or services in\n";
	print "                 the cluster that must be in a non-OK state\n";
	print "                 in order to result in a critical status level\n";
	print "-d               to enable debugging output\n";
	print "\n";
}
