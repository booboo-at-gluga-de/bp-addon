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

use lib ('/usr/local/bp-addon/lib/');
use strict;
use bsutils;
use dataBackend;
use settings;

my $settings = getSettings();
my $nagiosbpcfg="$settings->{'BP_ADDON_ETC'}/business-processes.conf";

if ( $ARGV[0] ne "" )
{
	$nagiosbpcfg=$ARGV[0];
}

my ($hardstates, $statusinfos, $tmp1, $tmp2, $in, @used_services, $i, $num_of_operators);
my $linenum=0;
my $rc=0;
my $undef_count=0;

($hardstates, $statusinfos) = &getStates();
#printHash($hardstates);

print "Checking consistency of $nagiosbpcfg\n";
open(IN, "<$nagiosbpcfg") or die "unable to read file $nagiosbpcfg\n";
	while($in = <IN>)
	{
		$linenum++;
		# exclude comments and empty lines
		if ($in !~ m/(^\s*#)|(^\s*$)/)
		{
			if ($in =~ m/^\s*display \d+;([A-Za-z0-9_-]+);/)
			{
				if (&checkForValidService($1) != 1)
				{
					print "   the display line on line $linenum uses a non existing business process: $1\n";
					$rc=1;
				}
			}
			elsif ($in =~ m/^\s*external_info ([A-Za-z0-9_-]+);/)
			{
				if (&checkForValidService($1) != 1)
				{
					print "   the external_info line on line $linenum uses a non existing business process: $1\n";
					$rc=1;
				}
			}
			elsif ($in =~ m/^\s*info_url ([A-Za-z0-9_-]+);/)
			{
				if (&checkForValidService($1) != 1)
				{
					print "   the info_url line on line $linenum uses a non existing business process: $1\n";
					$rc=1;
				}
			}
			elsif ($in =~ m/^\s*template ([A-Za-z0-9_-]+);/)
			{
				if (&checkForValidService($1) != 1)
				{
					print "   the template line on line $linenum uses a non existing business process: $1\n";
					$rc=1;
				}
			}
			elsif ($in =~ m/=/)
			{
				($tmp1, $tmp2) = split(/ *= */, $in);
				chomp($tmp2);
				$tmp2 =~ s/^ *\d+ *of: *//;

				# look if all used services are defined in Nagios
				@used_services = split(/ *&|\||\+ */, $tmp2);
				#print "$linenum: " . join(/ /, @used_services) . "\n";
				for ($i=0; $i<@used_services; $i++)
				{
					#if ($used_services[$i] !~ m/;/) { next; };
					$used_services[$i] =~ s/^ *//;
					$used_services[$i] =~ s/ *$//;
					if (&checkForValidService($used_services[$i]) == 0)
					{
						print "    Service \"$used_services[$i]\" used on line $linenum is not a defined anywhere\n";
						$undef_count++;
						$rc = 1;
					}
				}
				$tmp1 =~ s/^ *//;
				$tmp1 =~ s/ *$//;
				$hardstates->{$tmp1} = "DEFINED";
				#print "DEBUG: pushing $tmp1\n";

				# find formula with different operators
				$num_of_operators=0;
				if ($tmp2 =~ m/\|/) { $num_of_operators++ };
				if ($tmp2 =~ m/\+/) { $num_of_operators++ };
				if ($tmp2 =~ m/&/)  { $num_of_operators++ };
				if ($num_of_operators > 1)
				{
					print "    Line $linenum: Formula is mixing up different operators. This is not defined.\n";
					print "    " . $in;
					$rc = 1;
				}

				# find formula with "of:" and wrong operator
				if ($in =~ m/= *\d+ *of: */ && $in =~ m/&|\|/)
				{
					print "    Line $linenum: In a formula using the keyword \"of:\" the only allowed operator is +\n";
					print "    " . $in;
					$rc = 1;
				}
			}
			else
			{
				print "   Syntax Error on line $linenum:\n";
				print "   " . $in;
				$rc=1;
			}
		}
	}
close(IN);

if ($rc == 0)
{
	print "    OK\n";
}
elsif ($undef_count > 0)
{
	print "\n     Please note: You must define a host or service in nagios first of all,\n";
	print "     than You have to reload nagios, wait a minute and after this, You can use it\n";
	print "     in a Business Process.\n";
	print "     (The Nagios reload makes sure new defined services and hosts are known in\n";
	print "     NDO from where they are used by Business Processes.)\n\n";
}

#printHash($hardstates);
exit($rc);

sub checkForValidService()
{
	my $service = shift;

	if (defined $hardstates->{$service})
	{
		return(1);
	}
	else
	{
		return(0);
	}
}
