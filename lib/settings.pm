

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


package settings;

use Exporter;
use strict;
use lib ('/usr/local/bp-addon/lib/');
use bsutils;
our @ISA = qw(Exporter);
our @EXPORT = qw(getSettings getVersion);

my $settingsConf = "/usr/local/bp-addon/etc/settings.cfg";
my ($in, %settings, $var, $value);

sub getSettings()
{
	#print "DEBUG: Start of config\n";
	open(IN, "<$settingsConf") or die "unable to read file $settingsConf\n";
		while ($in = <IN>)
		{
			if ($in !~ m/(^\s*$|^\s*#)/)
			{
				#print "DEBUG: $in";
				chomp($in);
				($var, $value) = split(/=/, $in);
				$var = cutOffSpaces($var);
				$value = cutOffSpaces($value);
				#print "DEBUG: var   \"$var\"\n";
				#print "DEBUG: value \"$value\"\n";
				$settings{$var}=$value;
			}
		}
	close(IN);
	#print "DEBUG: End of config\n";
	return(\%settings);
}

sub getVersion() { return("0.9.7-alpha1"); }

1;
