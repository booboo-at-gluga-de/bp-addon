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


#Load modules
        use strict;
	use lib ('/usr/local/bp-addon/lib/');
	use settings;

#Configuration
	#default template which should be used for top level business processes
	#it has to be defined somewhere in nagios or icinga, e. g. services.cfg
	my $template_toplevel = "generic-bp-service";

	#default template which should be used for minor business processes
	#it has to be defined somewhere in nagios or icinga, e. g. services.cfg
	#may be the same als template_toplevel, if you do not want to have different
	#parameters for them
	my $template_minor = "generic-bp-detail-service";

#Parameters
	my ($in, $name, $description, $status, $nagios_bp_conf, $service_cfg, $help, $i, %individual_templates, $create_sub_bp, $output_file, $generate_notes);
	my $settings = getSettings();

	for ($i=0; $i<@ARGV; $i++)
	{
		if ($ARGV[$i] eq "-f")  { $nagios_bp_conf    = $ARGV[++$i] }
		if ($ARGV[$i] eq "-tt") { $template_toplevel = $ARGV[++$i] }
		if ($ARGV[$i] eq "-tm") { $template_minor    = $ARGV[++$i] }
		if ($ARGV[$i] eq "-s")  { $create_sub_bp     = $ARGV[++$i] }
		if ($ARGV[$i] eq "-o")  { $output_file       = $ARGV[++$i] }
		if ($ARGV[$i] eq "-n")  { $generate_notes    = $ARGV[++$i] }
		if ($ARGV[$i] eq "-h" || $ARGV[$i] eq "--help") { $help = 1 }
	}

	if ($create_sub_bp ne "0") { $create_sub_bp = 1 }
	if ($generate_notes ne "1") { $generate_notes = 0 }

#determin path/filename of resulting cfg file	
	if ($output_file eq "")
	{
		if ($nagios_bp_conf eq "")
		{
			# Default values if no config file is given
			$nagios_bp_conf = "$settings->{'BP_ADDON_ETC'}/nagios-bp.conf";
			$service_cfg = "$settings->{'NAGIOS_ETC'}/services-bp.cfg";
		}
		elsif ($nagios_bp_conf =~ m/.+\.conf$/)
		{
			#print "DEBUG: non standard config\n";
			$service_cfg = $nagios_bp_conf;
			$service_cfg =~ s#^.*/##;
			$service_cfg =~ s/\.conf$//;
			$service_cfg =~ s/^nagios-bp-?//;
			$service_cfg = "$settings->{'NAGIOS_ETC'}/services-bp-$service_cfg.cfg";
			#print "DEBUG: nagios_bp_conf $nagios_bp_conf\n";
			#print "DEBUG: service_cfg $service_cfg\n";
		}
	}
	else
	{
		$service_cfg = $output_file;
		if ($nagios_bp_conf eq "")
		{
			# Default values if no config file is given
			$nagios_bp_conf = "$settings->{'BP_ADDON_ETC'}/nagios-bp.conf";
		}
	}

#help
	if ($service_cfg eq "" || $help == 1)
	{
		print "\ncall using:\n";
		print "$0\n";
		print "for use with default parameters\n";
		print "(generate $settings->{'NAGIOS_ETC'}/services-bp.cfg from $settings->{'BP_ADDON_ETC'}/nagios-bp.conf\n";
		print "using default templates and default dummy hostnames)\n\n";
		print "or\n";
		print "$0 [-f \<config_file\>] [-tt \<template_toplevel\>] [-tm \<template_minor\>] [-o \<output_file\>] [-s 0|1] [-n 0|1]\n";
		print "where\n";
		print "\<config_file\>       is the file where You defined Your business processes\n";
		print "                    it must be named *.conf\n";
		print "\<template_toplevel\> is the service template You want to use for all business processes\n";
		print "                    displayed in the toplevel view\n";
		print "                    default: generic-bp-service\n";
		print "\<template_minor\>    is the service template You want to use for all other business processes\n";
		print "                    You may use the same value as for \<template_toplevel\>\n";
		print "                    default: generic-bp-detail-service\n";
		print "\<output_file\>       tells under which path and filename the resulting cfg file should be\n";
		print "                    generated\n";
		print "                    defaults to $settings->{'NAGIOS_ETC'}/services-bp.cfg if You use the default\n";
		print "                    config file (that means if You did not give -f parameter)\n";
		print "                    or to $settings->{'NAGIOS_ETC'}/services-bp-\<name_of_config_file\>.cfg\n";
		print "                    otherwise\n";
		print "-s 0                means: create services only for business processes displayed in\n";
		print "                    the top level view\n";
		print "-s 1                means: create services also for business processes with display 0\n";
		print "                    default is 1\n";
		print "-n 1                means: for each service we generate, this script should add an additional notes\n";
		print "                    line containing the description You did define in nagios-bp.conf\n";
		print "-n 0                means: do not add a notes line, this is the default\n";
		print "                    (same behavior as in versions up to 0.9.5)\n";
		print "\nFor further information see README, section \"Business Process representation as Nagios services\"\n\n";
		exit(1);
	}

#some infos on stdout
	print "\ngenerating $service_cfg from $nagios_bp_conf\n";
	if ($create_sub_bp == 1)
	{ 
		print "using templates $template_toplevel / $template_minor\n";
		print "services for sub-level Business Processes are also created\n\n";
	}
	else
	{ 
		print "using template $template_toplevel\n";
		print "service only for Business Processes of top level view are created\n\n";
	}


#parse nagios-bp.conf (our own config file)
	# look for bp's who have an own template defined
	open (IN, "<$nagios_bp_conf") or die "unable to read $nagios_bp_conf";
		while ($in = <IN>)
		{
			if ($in =~ m/^\s*template\s+/)
			{
				#print "DEBUG: $in";
				$in =~ s/^\s*template\s+//;
				($name, $description) = split(/;/, $in);
				chomp($description);
				#print "DEBUG name: $name desc:$description\n";
				$individual_templates{$name} = $description;
			}
		}
	close(IN);

	# make services for every bp named in a display statement
	open (IN, "<$nagios_bp_conf") or die "unable to read $nagios_bp_conf";
	open (OUT, ">$service_cfg") or die "unable to write to $service_cfg";
	print OUT '##################################################################################' . "\n";
	print OUT '#' . "\n";
	print OUT '# !!! DO NOT MODIFY THIS FILE !!!' . "\n";
	print OUT '#' . "\n";
	print OUT '# It is script generated!' . "\n";
	print OUT '# Change the file ' . "$nagios_bp_conf\n";
	print OUT '# and run the command ' . "$0 afterwards\n";
	print OUT '#' . "\n";
	print OUT '# If not doing so, Your changes will be lost on the next update' . "\n";
	print OUT '#' . "\n";
	print OUT '##################################################################################' . "\n\n\n";

	while ($in = <IN>)
	{
		# filter comments (starting with #) and blank lines
		if ($in !~ m/^#/ && $in !~ m/^ *$/)
		{
			#print "$in";
	
			# for all display definitions (lines starting with "display")
			if ($in =~ m/^\s*display\s+/)
			{
				$in =~ s/^\s*display\s+//;
				($status, $name, $description) = split(/;/, $in);
				chomp($description);
				#do not display business processes with status 0 if configured so (see section configuration)
				if ($status > 0 || $create_sub_bp == 1)
				{
					#print "$status : $name : $description\n";
                                        print OUT "define service{\n";
					if (defined $individual_templates{$name})
					{
                                        	print OUT "		use			$individual_templates{$name}\n";
					}
					elsif ($status > 0) 
					{ 
                                        	print OUT "		use			$template_toplevel\n";
					}
					else 
					{ 
                                        	print OUT "		use			$template_minor\n";
					}
                                        print OUT "		service_description	$name\n";
					if ($generate_notes == 1)
					{
						print OUT "		notes			$description\n";
					}
                                        print OUT "		check_command		check_bp_status!$name!$nagios_bp_conf\n";
                                        print OUT "		}\n\n";
				}
			}
		}
	}
	close(OUT);
	close(IN);

