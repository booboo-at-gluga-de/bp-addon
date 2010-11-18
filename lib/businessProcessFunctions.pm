

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


package businessProcessFunctions;

use lib ('/usr/local/bp-addon/lib/');
use Exporter;
use strict;
use bsutils;
use settings;
our $settings = getSettings();
our %i18n;
our @ISA = qw(Exporter);
our @EXPORT = qw(getBPs read_language_file get_lang_string getAvaiableLanguages and listAllComponentsOf);


#parse business-processes.conf (our own config file)
# parameter 1: the path of business-processes.conf file to be used
# parameter 2: a reference to the hardstates hash
#              this hash is extended by this function (states of business processes are added)
# parameter 3: "true" or "false", should external scripts be executed
#              defaults to "true"
# returns: hash reference with descriptions of all business processes
# returns: hash reference with priorities of all business processes
# returns: hash reference with the outputs of all external-info scripts
#          empty if parameter 3 is "false"
# returns: hash reference with all info-urls
# returns: hash reference with the formula for each business process
sub getBPs()
{
	my $nagios_bp_conf = shift;
	my $hardstates = shift;
	my $execute_external_scripts = shift || "true";

	my (@fields, @fields_state, $in, $formula, $num_of_operators, $result, %display_status, %display, %script_out, %info_url, %components, $description, $i, $min_ok, $name_ext, $name, $script, $status, $url, $var);

	open (IN, "<$nagios_bp_conf") or nagdie("unable to read $nagios_bp_conf");
	while ($in = <IN>)
	{
		# filter comments (starting with #) and blank lines
		if ($in !~ m/^#/ && $in !~ m/^ *$/)
		{
			#print "$in";

			# for all display definitions (lines starting with "display")
			if ($in =~ m/^display/)
			{
				$in = substr($in, 8);
				($status, $name, $description) = split(/;/, $in);
				chomp($description);
				$display{$name} = $description;
				$display_status{$name} = $status;
				#print "name: $name description: $description\n";
			}
	
			# for all external_info definitions (lines starting with "external_info")
			elsif ($in =~ m/^external_info/)
			{
				if ($execute_external_scripts ne "false")
				{
					$in = substr($in, 14);
					($name_ext, $script) = split(/;/, $in);
					chomp($script);
					open(SCRIPT, "$script |") or die "unable to execute script $script";
						$script_out{$name_ext} = <SCRIPT>;
					close(SCRIPT);
					#print "name: $name_ext out: $script_out{$name_ext}\n";
				}
			}
	
			# for all info_url definitions (lines starting with "info_url")
			elsif ($in =~ m/^info_url/)
			{
				$in = substr($in, 9);
				($name_ext, $url) = split(/;/, $in);
				chomp($url);
				$info_url{$name_ext} = $url;
			}

			else
			{
				# for all variable definitions (containing a =)
				if ($in =~ m/=/)
				{
					@fields = split(/ *= */, $in);
					$var = cutOffSpaces($fields[0]);
					if ($var =~ m/;/ ) { nagdie("variable names are not allowed to contain semicolon") }
					chomp($fields[1]);
					$formula = cutOffSpaces($fields[1]);

					$num_of_operators=0;
					if ($formula =~ m/\|/) { $num_of_operators++ };
					if ($formula =~ m/\+/) { $num_of_operators++ };
					if ($formula =~ m/&/) { $num_of_operators++ };
 					if ($num_of_operators > 1) { nagdie("no formulas mixing up the different operators") }
					# formulas containig only one element are used the same way as "and" formulas
					if ($formula !~ m/\|/ && $formula !~ m/&/ && $formula !~ m/\+/) { $formula .= " &" }
					#remember every single variable definition for later reverse lookup
					$components{$var} = $formula;

					# for formulas with "or"
					if ($formula =~ m/\|/)
					{
						@fields = split(/ *\| */, $formula);
						@fields_state = ();
						for ($i=0; $i<@fields; $i++)
						{
							@fields_state[$i] = $hardstates->{$fields[$i]};
							#print "$i: $fields[$i]: $hardstates{$fields[$i]}\n";
						}
						$result = &or(@fields_state);
						#print "$var $result\n";
						$hardstates->{$var} = $result;
					}
	
					# for formulas with "and"
					if ($formula =~ m/&/)
					{
						@fields = split(/ *& */, $formula);
						@fields_state = ();
						for ($i=0; $i<@fields; $i++)
						{
							@fields_state[$i] = $hardstates->{$fields[$i]};
							#print "$i: $fields[$i]: $hardstates{$fields[$i]}\n";
						}
						$result = &and(@fields_state);
						#print "$var $result\n";
						$hardstates->{$var} = $result;
					}

					# for formulas "x of y" (symbol +)
					if ($formula =~ m/\+/)
					{
						if ($formula =~ m/^(\d+) *of: *(.+)/)
						{
							$formula = $2;
							$min_ok = $1;
							@fields = split(/ *\+ */, $formula);
							@fields_state = ();
							for ($i=0; $i<@fields; $i++)
							{
								@fields_state[$i] = $hardstates->{$fields[$i]};
								#print "$i: $fields[$i]: $hardstates{$fields[$i]}\n";
							}
							$result = &x_of_y($min_ok, @fields_state);
							#print "debug: $var $result\n";
							$hardstates->{$var} = $result;
						}
						else
						{
							nagdie('syntax must be: <var> = <num> of: <var1> + <var2> [+ <varn>]*');
						}
					}
	
				}
			}

		}
	}
	close(IN);
	#&printHash(\%components, "DEBUG components: ");
	return(\%display, \%display_status, \%script_out, \%info_url, \%components);
}


# making an "and" conjuctions of states
sub and()
{
	my @params = @_;
	my %states = ( 0 => "UNKNOWN", 1 => "OK", 2 => "UNKNOWN", 3 => "WARNING", 4 => "CRITICAL" );
	my %statesrev = ( "OK" => 1, "UNKNOWN" => 2, "WARNING" => 3, "CRITICAL" => 4);
	my $i;
	my $max = 0;
	my $value;

	for ($i=0; $i<@params; $i++)
	{
		$value = $statesrev{$params[$i]};
		if ($value eq "") {$value = 2}
		if ($value > $max) { $max = $value }
		#print "$params[$i]: $value\n";
	}

	#return
	$states{$max};
}

# making an "or" conjuctions of states
sub or()
{
	my @params = @_;
	my %states = ( 1 => "OK", 2 => "UNKNOWN", 3 => "WARNING", 4 => "CRITICAL", 5 => "UNKNOWN" );
	my %statesrev = ( "OK" => 1, "UNKNOWN" => 2, "WARNING" => 3, "CRITICAL" => 4);
	my $i;
	my $min = 5;
	my $value;

	for ($i=0; $i<@params; $i++)
	{
		$value = $statesrev{$params[$i]};
		if ($value eq "") {$value = 2}
		if ($value < $min) { $min = $value }
		#print "$params[$i]: $value\n";
	}

	#return
	$states{$min};
}

# making an "x_of_y" conjuctions of states
sub x_of_y()
{
	my @params = @_;
	my $i;
	my %state_counts;
	my $return = "UNKNOWN";
	my $min_ok = shift(@params);
	#print "min_ok: $min_ok\n";

	for ($i=0; $i<@params; $i++)
	{
		$state_counts{$params[$i]}++;
		#print "parm $i: \"$params[$i]\"\n";
	}

	if ($state_counts{"OK"} >= $min_ok) { $return="OK" }
	elsif ($state_counts{"OK"} + $state_counts{"WARNING"} >= $min_ok) { $return="WARNING" }
	else { $return="CRITICAL" }

	#return
	$return;
}

# internationalization: read the different output strings in a given language
# and store the strings in global hash i18n
# there it can be accessed by get_lang_string()
# param 1: the language, can be a single language abreviation like "de", "en",...
#          or a string like a Accept-Language HTTP Header
#          HTTP_ACCEPT_LANGUAGE='en,en-us;q=0.8,de-de;q=0.5,de;q=0.3'
# param 2: default language e. g. "en"
#          if the given language is unavailable
sub read_language_file()
{
	my $lang = shift;
	my $default_lang = shift;

	my ($in, $name, $value, $filename, @languagepriority, $i, @searchresult, $available_lang);

	die "default_lang is not valid\n" if ($default_lang !~ m/^[a-z][a-z]$/);

	chomp($lang);

	$available_lang = &getAvaiableLanguages();

	#print "lang: $lang\n";
	#print "default_lang: $default_lang\n";
	#print "available_lang: " . join(", ", @$available_lang) . "\n";

	# extract language out of accept language header
	if ($lang !~ m/^[a-z][a-z]$/)
	{
		#print "lang: $lang\n";
		@languagepriority = split(/[,;]/, $lang);
		for ($i=0; $i<@languagepriority; $i++)
		{
			next if ($languagepriority[$i] =~ m/^q=/);
			$languagepriority[$i] =~ s/-[a-z][a-z]//;
			next if ($languagepriority[$i] !~ m/^[a-z][a-z]$/);
			#print "$languagepriority[$i]\n";
			@searchresult = grep(/$languagepriority[$i]/, @$available_lang);
			#print scalar @searchresult . "\n";
			if (@searchresult > 0)
			{
				$lang = $languagepriority[$i];
				last;
			}
		}
	}
	if ($lang !~ m/^[a-z][a-z]$/)
	{
		$lang = $default_lang;
	}
	#print "lang: $lang\n";

	# load the best matching language file
	$filename = "$settings->{'BP_ADDON_LANG'}/i18n_$lang.txt";

	if ( ! -r $filename )
	{
		$lang = $default_lang;
		$filename = "$settings->{'BP_ADDON_LANG'}/i18n_$lang.txt";
	}

	open(IN, "<$filename") or die "unable to read language file $filename\n";
		while($in = <IN>)
		{
			if ($in !~ m/^\s*#/ && $in !~ m/^\s*$/)
			{
				#print $in;
				chomp($in);
				($name, $value) = split(/\s*=\s*/, $in);
				#print "name: $name, value: $value\n";
				$i18n{$name} = $value;
			}
		}
	close(IN);

	return(1);
}

sub get_lang_string()
{
	my $string = shift;
	my $substituted = "";
	my $i=1;
	my $var="";

	if (defined $i18n{$string})
	{
		# allow variable susbstitution
		$substituted = $i18n{$string};
		while ($var = shift)
		{
			$substituted =~ s/__var${i}__/$var/g;
			$i++;
		}

		return($substituted);
	}
	else
	{
		return($string);
	}
}

# build a list of available languages
sub getAvaiableLanguages()
{
	my (@available_lang, $fname);

	opendir(DIR, $settings->{'BP_ADDON_LANG'}) or die "unable to open directory for language files $settings->{'BP_ADDON_LANG'}\n";
		while ($fname = readdir(DIR))
		{
			if (-f "$settings->{'BP_ADDON_LANG'}/$fname" && $fname =~ m/i18n_([a-z][a-z]).txt$/)
			{
				#print "available_lang: $1\n";
				push(@available_lang, $1);
			}
		}
	closedir(DIR);

	return(\@available_lang);
}

sub nagdie()
{
	print $_[0] . "\n";
	exit(3);
}

sub listAllComponentsOf()
{
	my $bp = shift;
	my $bps_hashref = shift;
	
	my (@act_bp_components, $k, %result_list, $act_component, $bps_left_in_result);
	
	#print "DEBUG starting func listAllComponentsOf for $bp\n";
	$result_list{$bp} = 1;
	$bps_left_in_result = 1;
	#print "DEBUG func bp: resultlist now contains $bps_left_in_result bps:\n";
	#printHash(\%result_list);

	while ($bps_left_in_result > 0)
	{
		$bps_left_in_result = 0;
		foreach $act_component (keys %result_list)
		{
			if ($act_component !~ m/;/)
			{
				$bps_left_in_result++;
				#print "DEBUG func bp: is bp $act_component\n";
				$bps_hashref->{$act_component} =~ s/\s*\d+\s+of:\s*//;
				@act_bp_components = split(/\s*&|\||\+\s*/, $bps_hashref->{$act_component});
				#print "DEBUG func bp: $act_component contains " . join(/,/, @act_bp_components) . "\n";
				#print "DEBUG func bp: deleting \"$act_component\"\n";
				delete($result_list{$act_component});

				for ($k=0; $k<@act_bp_components; $k++)
				{
					$act_bp_components[$k] = cutOffSpaces($act_bp_components[$k]);
					#print "DEBUG func bp: adding \"$act_bp_components[$k]\"\n";
					$result_list{$act_bp_components[$k]} = 1;
				}
			}
		}
		#print "DEBUG func bp: there were $bps_left_in_result bps\n";
		#print "DEBUG func bp: resultlist now contains:\n";
		#printHash(\%result_list);
	}
	#foreach $act_bp (keys %$bps_hashref)
	#{
	#	print "DEBUG func act_bp: $act_bp\n";
	#	#printArray(\@act_bp_components);
	#	for ($k=0; $k<@act_bp_components; $k++)
	#	{
	#	       $act_bp_components[$k] = &cutOffSpaces($act_bp_components[$k]);
	#	       #print "DEBUG func:    act_bp_components \"$act_bp_components[$k]\"\n";
	#	}
	#	#@match = grep(/^$search$/, @component_list);
	#	#printArray(\@match);
	#}
	
	return(keys %result_list);
}

return(1);
