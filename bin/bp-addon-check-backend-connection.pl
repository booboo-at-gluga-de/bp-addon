#!/usr/bin/perl

#    Nagios Business Process View and Nagios Business Process Analysis
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

use lib ('/usr/local/bp-addon/lib/');
use strict;
use bsutils;
use dataBackend;
use settings;

#my $settings = getSettings();
#my $nagiosbpcfg="$settings->{'BP_ADDON_ETC'}/nagios-bp.conf";

my ($hardstates, $statusinfos, $key, $maxlen, %dbparam);
my %backend_description = ( 
	"db" => "NDO Database", 
	"merlin" => "Merlin Database", 
	"fs" => "NDO2FS Filesystem", 
	"mk_livestatus" => "mk_livestatus", 
	"icinga-web" => "Icinga-Web API HTTP/JSON"
);

($hardstates, $statusinfos) = &getStates();
%dbparam = &getBackendParam();

#printHash($hardstates);
#printHash($statusinfos);

print "\nReport of actual status information\n";
print "-----------------------------------\n\n";
print "DataBackend is $dbparam{'backend'} ($backend_description{$dbparam{'backend'}})\n";
print "which got it's last update at " . &getLastUpdateServiceStatus() . "\n\n";

foreach $key (keys %$statusinfos)
{
	if (length($key) > $maxlen)
	{
		$maxlen = length($key);
	}
}
#print "max: $maxlen\n";

foreach $key (sort keys %$statusinfos)
{
	#if ($key !~ m/business_process/)
	#{
		print fixedLen("[$key]", $maxlen+2, "left") . " [" . fixedLen($hardstates->{$key}, 8, "right") . "] $statusinfos->{$key}\n";
	#}
}
