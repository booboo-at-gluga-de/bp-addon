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


# helper script for testing e. g. plugin timeouts
# (just gets a lock and holds it for 300 sec)

use strict;
use Fcntl qw(:DEFAULT :flock);

my $servicelist="/usr/local/ndo2fs/var/VOLATILE/default/VIEWS/SERVICELIST";

open (LIST, "<$servicelist") or die "unable to read from file $servicelist\n";
flock(LIST, LOCK_EX);
sleep 300;
close(LIST);
