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
	use lib ('/usr/local/bp-addon/lib/');
        #CGI-Modul
        use CGI;
        #restrict maximum size of posted data
        $CGI::POST_MAX=5000;
        #disallow uploads
        $CGI::DISABLE_UPLOADS=1;
        #log to the log of webserver
        use CGI::Carp;
        #require a good programming
        use strict;
	#cgi simple for url encoding and decoding
	use CGI::Simple;
	#some useful functions
	use bsutils;
	#functions for getting states from the ndo database
	use dataBackend;
	#functions for parsing nagios_bp_config file
	use businessProcessFunctions;
	#get installation specific parameters: path variables and so on
	use settings;
	#for JSON import/export
	use JSON::XS;
	#for debug only
	#use Data::Dumper;


#some Variables
	my $settings = getSettings();
	# where is the cgi.cfg file located?
	# from this we take the credentials and location of the database
	my $nagios_bp_conf = $settings->{'BP_ADDON_ETC'} . "/";
	my $own_url = $ENV{"SCRIPT_NAME"};
	my $rowcount = 0;
	my $session_dir = $settings->{'BP_ADDON_VAR'} . "/nagios_bp.sessions";
	my $new_session = 0;
	my $cgi_cfg_file = $settings->{'NAGIOS_ETC'} . "/cgi.cfg";
	my $default_language = "de";
	my $cgi_simple = new CGI::Simple;       #Instance of CGI simple
        my $query = new CGI;                    #Instance of CGI module
	my %trafficlight_linkmap = ( "yes" => "yes", "no" => "no", "short" => "no", "only" => "yes" );

	my ($in, $i, $j, $its_in, $key, @fields_state, $hardstates, $statusinfos, $rowclass, $components, $display, $display_status, @services, @aggregations, $aggregation, $host, $service, $service_for_url, $operator, $title, $prev_host, $script_out, $info_url, %dbparam, $param, $value, $dbh, $sql, $sth , $min_ok, $tmp_host, $tmp_service, $traffic_light_prio, $db_prefix, $RC, $nagios_check_cmd, $language, $languages, @defined_priorities, @used_priorities, $prio, %json, %json_data, $json_coder, @localtime, $timestamp);


#query parameters
	# in this parameter you can give the name of a business process
	# if set, print out detail view of this business process
        my $detail = $query->param("detail");
	# in this parameter you can give the name of a business process
	# if set, print out tree view of this business process
        my $tree = $query->param("tree");
	# with this parameter you decide, if you want to display the traffic light showing infos for each prio in total
	# my be "yes" display it together with the other view
	# or "no" do not display
	# or "only" display traffic light only
	# or "short" display traffic light only without headline
        my $trafficlight = $query->param("trafficlight");
	# which configfile do we work on
        my $conf = $query->param("conf");
	# there are two modes "act" works on actual states from nagios, this one is the default
	# "bi" is the business impact analysis and works on states set by the user
        my $mode = $query->param("mode");
	# sessions are only used in mode "bi"
        my $sessionid = $query->param("sessionid");
	# base is defined only in mode "bi" and only necessary in the beginning of a business impact analysis
	# "act" tells to start with the actual values for each component 
	# "ok" tells to start with all components set to ok state 
        my $base = $query->param("base");
	# set is used in mode "bi" to set a state
	my $set = $query->param("set");
	# to can be used with set and is a value to which the state should be set
	my $to = $query->param("to");
	# lang can be used if you want to use a dedicated language, not the language submitted in Accept Language Header
	my $lang = $query->param("lang");
	# with disprio you can tell the overview page to just display one single priority
	my $display_prio = $query->param("disprio");
	# decides if the output is created as html (for display directly in a browser) or json (for use in scripts, etc.)
	# possible valuse are "html" or "json", defaults to "html"
	my $output_format = $query->param("outformat");


#set defaults
	if ($mode ne "bi") { $mode = "act" }
	if ($trafficlight ne "yes" && $trafficlight ne "only" && $trafficlight ne "short") { $trafficlight = "no" }
	if ($base ne "ok" && $base ne "" ) { $base = "act" }
	if ($to ne "" && $to !~ m/^(OK|WARNING|CRITICAL|UNKNOWN)$/ ) { $to = "UNKNOWN" }
	$set =~ s/(\/|\.\.|<|>)//g;
	if ($sessionid !~ m/^[0-9]+\.[0-9]+$/ ) { $sessionid = "" }
	if ($detail eq "" || $detail !~ m/^[a-zA-Z0-9_\-]+$/ ) { $detail = "none" }
	if ($tree eq "" || $tree !~ m/^[a-zA-Z0-9_\-]+$/ ) { $tree = "none" }
	if ($conf eq "" || $conf !~ m/^[a-zA-Z0-9_\-]+$/ ) { $conf = "nagios-bp" }
	$nagios_bp_conf .= $conf . ".conf";
	if ($display_prio !~ m/^[0-9]+$/ ) { $display_prio = "all" }
	if ($output_format ne "json" ) { $output_format = "html" }

	@localtime = localtime(time);
	$localtime[0] = sprintf("%02d", $localtime[0]);
	$localtime[1] = sprintf("%02d", $localtime[1]);
	$localtime[2] = sprintf("%02d", $localtime[2]);
	$localtime[3] = sprintf("%02d", $localtime[3]);
	$localtime[4] = sprintf("%02d", ++$localtime[4]);
	$localtime[5] += 1900;
	$timestamp = "$localtime[5]-$localtime[4]-$localtime[3] $localtime[2]:$localtime[1]:$localtime[0]";


#load korrekt i18n language file
	#print "Content-Type: text/plain\n\n";
	if ($lang =~ m/^[a-z][a-z]$/) 
	{ 
		&read_language_file($lang, $default_language);
	}
	else
	{
		&read_language_file($ENV{"HTTP_ACCEPT_LANGUAGE"}, $default_language);
	}


# error handling
	# parameter conf
	if ( ! -f $nagios_bp_conf || ! -r $nagios_bp_conf )
	{
		&printPageHead("html", "norefresh");
		print "<div class=\'statusTitle\' id=\'nbp_error_head\'>" . &get_lang_string("error_wrong_parameter_conf_head") . "</div>\n";
		print "<p id=\'nbp_error_text\'>\n";
		print &get_lang_string("error_wrong_parameter_conf_body", $nagios_bp_conf) . "\n";
		print "</p>\n";
		&printPageFoot("html");
		exit(0);
	}

	# check if Nagios is running
	open (IN, "<$cgi_cfg_file") or die "unable to read Nagios CGI configfile $cgi_cfg_file\n";
		while ($in = <IN>)
		{
			if ($in =~ m/\s*nagios_check_command\s*=\s*(.+)/)
			{
				#print "$in";
				#print "1: $1\n";
				$nagios_check_cmd = $1;
			}
		}
	close(IN);

	if ($nagios_check_cmd eq "")
	{
		$RC=0;
	}
	else
	{
		#$RC=system('/usr/local/nagios/libexec/check_nagios_with_db -e 3 -C \'/usr/local/nagios/bin/nagios -d\'');
		$RC=system($nagios_check_cmd . ">/dev/null");
	}

	if ($RC != 0)
	{
		&printPageHead("html");
		print "<p id=\'nbp_error_text\'>\n";
		print &get_lang_string("error_nagios_not_running") . "\n";
		print "</p>\n";
		&printPageFoot("html");
		exit(0);
	}


#read the status data
	if ($mode eq "act")
	{
		# in mode act, read from the db
		($hardstates, $statusinfos) = &getStates();
	}
	else
	{
		# in mode bi it depends...
		if ($base eq "" && $sessionid ne "")
		{
			# ... on a existing session take states from the peristent files
			&loadSession($sessionid);
		}
		else
		{
			if ($sessionid eq "")
			{
				# create a session id
				$sessionid=time . ".$$";
				$new_session=1;
			}

			# ... on a new session, we read from the db
			($hardstates, $statusinfos) = &getStates();

			# even if we start with all komponents set to ok, we take the states from the db and overwrite
			# where necessary here, this way we get quite good statusinfos
			if ($base eq "ok")
			{
				foreach $key (keys %$hardstates)
				{
					if ($hardstates->{$key} ne "OK")
					{
						$hardstates->{$key}="OK";
						$statusinfos->{$key}=&get_lang_string("manually_set_to_ok");
					}
				}
			}

			# save the session
			&saveSession($sessionid);
		}
	}

# process the given nagios_bp_conf file

	($display, $display_status, $script_out, $info_url, $components) = &getBPs($nagios_bp_conf, $hardstates);

	# look which priorities are defined
        foreach $key (sort keys %$display)
        {
		$defined_priorities[$display_status->{$key}] = 1 if ($display_status->{$key} != 0);
	}

	#print "Priorities:\n";
	#for ($i=0; $i<@defined_priorities; $i++)
	#{
	#	if (defined $defined_priorities[$i])
	#	{
	#		print "$i\n";
	#	}
	#}

	# compute the status for a whole prio (for traffic light)
	##print "Content-Type: text/html\n\n";
	for ($traffic_light_prio=1; $traffic_light_prio<=@defined_priorities; $traffic_light_prio++)
	{
		if (defined $defined_priorities[$traffic_light_prio])
		{
			@fields_state = ();
		        foreach $key (sort keys %$display)
		        {
				if ($display_status->{$key} == $traffic_light_prio)
				{
					#print "$traffic_light_prio: $key $display_status->{$key} $hardstates{$key}<br>\n";
					push (@fields_state, $hardstates->{$key});
				}
			}
			$hardstates->{"__prio$traffic_light_prio"} = &and(@fields_state);
			#print "result $traffic_light_prio: " . $hardstates->{"__prio$traffic_light_prio"} . "\n";
		}
	}


# in mode "bi" set the submitted state, if there is one
	if ( $mode eq "bi" && $set ne "" && $to ne "" )
	{
		$set = $cgi_simple->url_decode($set);
		#print "Content-Type: text/html\n\n";
		#print "setting $set to $to<br><br>\n";
		if ($set =~ m/;/)
		{
			$hardstates->{$set}=$to;
			$statusinfos->{$set}=&get_lang_string("manually_set_to", $to);
		}
		else
		{
			foreach $key (sort keys %$hardstates)
			{
				if ($key =~ m/^$set;/)
				{
					$hardstates->{$key}=$to;
					$statusinfos->{$key}=&get_lang_string("manually_set_to", $to);
				}
			}
		}
		&saveSession($sessionid);
	}

# print out the results as an HTML page
	if ( $mode eq "bi" && $base eq "" && $new_session == 1 )
	{
		# page: select starting point for business impact analysis

		&printPageHead("html");
		print "		<div class=\'statusTitle\' id=\'nbp_head_bi\'>". &get_lang_string("bi_head") ."</div>\n";
		print " 	<p class=\'nbp_text_small\'>" .  &get_lang_string("bi_explanation") . "</p>\n";
		print " 	<p class=\'nbp_sub_head\'>" .  &get_lang_string("bi_start_session") . "</p>\n";
		print " 	<span class=\'nbpText\'>" .  &get_lang_string("bi_select_starting_point") . "</span>\n";
		print " 	<form action=\"$own_url\" method=\"get\" id=\'nbp_startingpoint_form_bi\'>\n";
		print " 		<input type=\"hidden\" name=\"conf\" value=\"$conf\">\n";
		print " 		<input type=\"hidden\" name=\"mode\" value=\"$mode\">\n";
		print " 		<input type=\"hidden\" name=\"lang\" value=\"$lang\">\n";
		print " 		<input type=\"hidden\" name=\"sessionid\" value=\"$sessionid\">\n";
		print " 		<input type=\"hidden\" name=\"trafficlight\" value=\"$trafficlight\">\n";
		print " 		<input type=\"hidden\" name=\"disprio\" value=\"$display_prio\">\n";
		print " 		<input type=\"radio\" name=\"base\" value=\"act\" checked=\"checked\"> " .  &get_lang_string("bi_actual_state") . "<br>\n";
		print " 		<input type=\"radio\" name=\"base\" value=\"ok\"> " .  &get_lang_string("bi_all_set_to_ok") . "<br><br>\n";
		print " 		<input type=\"submit\" value=\"OK\">\n";
		print " 	</form>\n";
		print " 	<p class=\'nbp_text_small\'>" .  &get_lang_string("bi_hint_session_timeout") . "</p>\n";
		&printPageFoot("html");
		
	}
	elsif ( $mode eq "bi" && $set ne "" && $to eq "")
	{
		# page: set new state for host/service in business impact analysis

		&printPageHead("html");
		($tmp_host, $tmp_service) = split(/;/, $set);
		print "		<div class=\'statusTitle\' id=\'nbp_head_bi\'>" .  &get_lang_string("bi_head") . ": " .  &get_lang_string("bi_set_status") . "</div>\n";
		if ($tmp_service eq "")
		{
			print " 	<span class=\'nbpText\'>" .  &get_lang_string("bi_set_host_status_to", $tmp_host) . "</span><br>\n";
		}
		else
		{
			print " 	<span class=\'nbpText\'>" .  &get_lang_string("bi_set_service_status_to", $tmp_service, $tmp_host) . "</span><br>\n";
		}
		print " 	<form action=\"$own_url\" method=\"get\" id=\'nbp_select_state_form_bi\'>\n";
		print " 		<input type=\"hidden\" name=\"conf\" value=\"$conf\">\n";
		print " 		<input type=\"hidden\" name=\"mode\" value=\"$mode\">\n";
		print " 		<input type=\"hidden\" name=\"lang\" value=\"$lang\">\n";
		print " 		<input type=\"hidden\" name=\"detail\" value=\"$detail\">\n";
		print " 		<input type=\"hidden\" name=\"tree\" value=\"$tree\">\n";
		print " 		<input type=\"hidden\" name=\"sessionid\" value=\"$sessionid\">\n";
		print " 		<input type=\"hidden\" name=\"trafficlight\" value=\"$trafficlight\">\n";
		print " 		<input type=\"hidden\" name=\"disprio\" value=\"$display_prio\">\n";
		print " 		<input type=\"hidden\" name=\"set\" value=\"" . $cgi_simple->url_encode($set) . "\">\n";
		print " 		<input type=\"radio\" name=\"to\" value=\"OK\" checked=\"checked\"> OK<br>\n";
		print " 		<input type=\"radio\" name=\"to\" value=\"WARNING\"> WARNING<br>\n";
		print " 		<input type=\"radio\" name=\"to\" value=\"CRITICAL\"> CRITICAL<br>\n";
		print " 		<input type=\"radio\" name=\"to\" value=\"UNKNOWN\"> UNKNOWN<br><br>\n";
		print " 		<input type=\"submit\" value=\"OK\">\n";
		print " 	</form>\n";
		&printPageFoot("html");
	}
	else
	{
		if ( $detail eq "none" )
		{
			if ( $tree eq "none" )
			{
				if ( $output_format eq "html" )
				{
					# Display the default view (overview page) in html

					&printPageHead("html");
					print "		<div id=\'nbpTopLevelBox\'>\n";
	
					if ( $trafficlight eq "yes" || $trafficlight eq "only" || $trafficlight eq "short")
					{
						# display the traffic light section
						print "			<div id=\"nbp_trafficlight_${trafficlight}_box\">\n";
						print "				<div class=\'statusTitle\' id=\'nbp_trafficlight_${trafficlight}_head\'>" .  &get_lang_string("short_summary_head") . "</div>\n";
						print " 			    <table class=\'status\' id=\'nbp_trafficlight_${trafficlight}_table\'>\n";
						print " 				<tr>\n";
						print " 					<th class=\'status\'><a class=\'status\' href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=$trafficlight_linkmap{$trafficlight}&amp;disprio=all\">" .  &get_lang_string("prio") . "</a></th>\n";
						print " 					<th class=\'status\'>" .  &get_lang_string("status") . "</th>\n";
						print " 				</tr>\n";

						for ($traffic_light_prio=1; $traffic_light_prio<=@defined_priorities; $traffic_light_prio++)
						{
							if (defined $defined_priorities[$traffic_light_prio])
							{
								if ($traffic_light_prio%2 == 0) { $rowclass = "statusEven" }
								else { $rowclass = "statusOdd" }
								print " 				<tr>\n";
								print "						<td class=\'$rowclass\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=$trafficlight_linkmap{$trafficlight}&amp;disprio=$traffic_light_prio\">" .  &get_lang_string("prio") . " $traffic_light_prio</a></td>\n";
								print "						<td class=\'miniStatus" .$hardstates->{"__prio$traffic_light_prio"} . "\'>" .$hardstates->{"__prio$traffic_light_prio"} . "</td>\n";
								print " 				</tr>\n";
							}
						}
	
						print " 			    </table>\n";
						print " 			</div>\n";
					}
	
					if ( $trafficlight eq "yes" || $trafficlight eq "no" )
					{
						# main tree view area
						print "		<div id=\"nbp_cental_table_box_tl_${trafficlight}\">\n";
						print "		<div class=\'statusTitle\' id=\'nbp_head_${mode}\'>";
						if ($mode eq "act") 
						{ 
							print &get_lang_string("short_summary_head") . ": " .  &get_lang_string("all_bp") 
						}
						elsif ($mode eq "bi") 
						{ 
							print &get_lang_string("bi_head") . ": " .  &get_lang_string("all_bp") 
						}	
						if ($display_prio ne "all")
						{
							print " - " . &get_lang_string("priority_" . $display_prio . "_headline");
						}
						print "</div>\n";
						print " 	<div id=\'nbp_central_element\'>\n";
						print " 		<table id=\'nbp_central_table\' class=\'status\'>\n";

						if ($display_prio eq "all")
						{
							for ($prio=1; $prio<@defined_priorities; $prio++)
							{
								if (defined $defined_priorities[$prio])
								{
									&displayPrio($prio);
								}
							}
						}
						else
						{
							if (defined $defined_priorities[$display_prio])
							{
								&displayPrio($display_prio);
							}
						}
	
						print "			</table>\n";

						# buttons below main tree view table: prio selection
						print "			<div id=\'nbp_button_bar\'>\n";
						print "			<span id=\'nbp_prio_selection\'>\n";
						if ($display_prio eq "all")
						{
							print "			<span class=\"nbp_nobr\">[" .  &get_lang_string("all_prios") . "]</span>\n";
						}
						else
						{
							print "			<span class=\"nbp_nobr\"><a href=\"$own_url?conf=$conf&amp;ode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=$trafficlight&amp;disprio=all\">[" .  &get_lang_string("all_prios") . "]</a></span>\n";
						}
						for ($prio=1; $prio<@defined_priorities; $prio++)
						{
							if (defined $defined_priorities[$prio])
							{
								if ($display_prio == $prio)
								{
									print "			<span class=\"nbp_nobr\">[" .  &get_lang_string("prio") . " $prio]</span>\n";
								}
								else
								{
									print "			<span class=\"nbp_nobr\"><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=$trafficlight&amp;disprio=$prio\">[" .  &get_lang_string("prio") . " $prio]</a></span>\n";
								}
							}
						}
						print "			</span>\n";

						# buttons below main tree view table to switch traffic light on/off
						print "			<span id=\'nbp_trafficlight_switch\'>\n";
						if ($trafficlight eq "yes")
						{
							print "			<span class=\"nbp_nobr\"><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=no&amp;disprio=$display_prio\">[" .  &get_lang_string("hide_trafficlight") . "]</a></span>\n";
						}
						else
						{
							print "			<span class=\"nbp_nobr\"><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;lang=$lang&amp;trafficlight=yes&amp;disprio=$display_prio\">[" .  &get_lang_string("show_trafficlight") . "]</a></span>\n";
						}
						print "			</span>\n";
						print "			</div>\n";
						print "		</div>\n";
						print "		</div>\n";
					}

					print "	</div>\n";
					&printPageFoot("html");
				}
				else
				{
					# Display the default view in json 
					# (all business processes, all sub processes with all information)

					&printPageHead("json");

					foreach $key (sort keys %$display)
					{
						chomp($script_out->{$key});
						my (%tmp_hash, @tmp_array);

						if ($components->{$key} =~ m/&/) { $operator = "and" }
						elsif ($components->{$key} =~ m/\+/) { $operator = "of" }
						else { $operator = "or" }
						undef $min_ok;
						if ($operator eq "of")
						{
							$components->{$key} =~ m/^(\d+) *of: *(.+)/;
							$min_ok = $1;
							$components->{$key} = $2;
						}
						@services = split(/ *&|\||\+ /, $components->{$key});
						for ($i=0; $i<@services; $i++)
						{
							$services[$i] = &cutOffSpaces($services[$i]);

							my %tmp_hash2;
							# print "\n";

							if ( $services[$i] =~ m/;/ )
							{
								# this output, if it is a single service
								($host, $service) = split(/;/, $services[$i]);
								# print "host:          $host\n";
								# print "service:       $service\n";
								$tmp_hash2{"host"}     = $host;
								$tmp_hash2{"service"}  = $service;
							}
							else
							{
								# this output, if it is an aggregated service
								# print "subprocess:    $services[$i]\n";
								# print "displayname:   $display->{$services[$i]}\n";
								# print "external_info: $script_out->{$services[$i]}\n" if (defined $script_out->{$services[$i]});

								$tmp_hash2{"subprocess"}    = $services[$i];
								$tmp_hash2{"display_prio"}  = $display_status->{$services[$i]};
								$tmp_hash2{"display_name"}  = $display->{$services[$i]};
								$tmp_hash2{"info_url"}      = $info_url->{$services[$i]} if (defined $info_url->{$services[$i]});
								$tmp_hash2{"external_info"} = $script_out->{$services[$i]} if (defined $script_out->{$services[$i]});
							}
							# print "hardstate:     $hardstates->{$services[$i]}\n";
							# print "statusinfo:    $statusinfos->{$services[$i]}\n" if (defined $statusinfos->{$services[$i]});
	
							$tmp_hash2{"hardstate"}     = $hardstates->{$services[$i]};
							$tmp_hash2{"plugin_output"} = $statusinfos->{$services[$i]} if (defined $statusinfos->{$services[$i]});
	
							push(@tmp_array, \%tmp_hash2);
						}

						#print "bp_id: $key\n";
						#print "    display_prio:  $display_status->{$key}\n";
						#print "    display_name:  $display->{$key}\n";
						#print "    hardstate:     $hardstates->{$key}\n";
						#print "    info_url:      $info_url->{$key}\n";
						#print "    external_info: $script_out->{$key}\n";
						#print "    components:    $components->{$key}\n";
						#print "    operator:      $operator\n";
						#print "    min_ok:        $min_ok\n\n";

						$tmp_hash{"display_prio"}  = $display_status->{$key};
						#if ($display_status->{$key} != 0)
						#{
						#	$tmp_hash{"display_prio_headline"}    = &get_lang_string("priority_" . $display_status->{$key} . "_headline");
						#	$tmp_hash{"display_prio_description"} = &get_lang_string("priority_" . $display_status->{$key} . "_description");
						#}
						$tmp_hash{"display_name"}  = $display->{$key};
						$tmp_hash{"hardstate"}     = $hardstates->{$key};
						$tmp_hash{"info_url"}      = $info_url->{$key} if (defined $info_url->{$key});
						$tmp_hash{"external_info"} = $script_out->{$key} if (defined $script_out->{$key});
						$tmp_hash{"components"}    = \@tmp_array;
						$tmp_hash{"operator"}      = $operator;
						$tmp_hash{"min_ok"}        = $min_ok if (defined $min_ok);

						$json_data{$key} = \%tmp_hash;
					}

					$json{'business_processes'} = \%json_data;
					$json{'priority_definitions'} = getPriorityDescriptions(@defined_priorities);
					$json{'json_created'} = $timestamp;

					#print "\n\nDEBUG:\n";
					#printHash(\%json);
					#print "\n\nDEBUG dump:\n";
					#print Dumper(\%json);
					#print "\n\nDEBUG JSON:\n";
					#print encode_json(\%json);
					$json_coder = JSON::XS->new->ascii->pretty->allow_nonref;
					print $json_coder->encode (\%json);
					print "\n";

					&printPageFoot("json");
				}
			}
			else
			{
				# Display the tree view

				#print "tree: $tree\n";
				#print "components: $components->{$tree}\n";
				if ($components->{$tree} =~ m/&/) { $operator = "and" }
				elsif ($components->{$tree} =~ m/\+/) { $operator = "of" }
				else { $operator = "or" }

				undef $min_ok;
				if ($operator eq "of")
				{
					$components->{$tree} =~ m/^(\d+) *of: *(.+)/;
					$min_ok = $1;
					$components->{$tree} = $2;
				}
				#print "op: $operator\n";
				@services = split(/ *&|\||\+ /, $components->{$tree});

				# check if the requested business process is defined 
				if ( ! defined $display->{$tree} )
				{
					&printPageHead("html", "norefresh");
					print "<div class=\'statusTitle\' id=\'nbp_error_head\'>" . &get_lang_string("error_bp_not_existing") . "</div>\n";
					print "<p id=\'nbp_error_text\'>\n";
					print &get_lang_string("error_bp_not_existing_body", $tree) . "\n";
					print "</p>\n";
					&printPageFoot("html");
					exit(0);
				}

				if ( $output_format eq "html" )
				{
					# Display tree view in HTML (in every page below top level)
	
					&printPageHead("html");
					print "		<div id=\"nbp_single_table_box\">\n";
					print "		<div class=\'statusTitle\'>";
					if ($mode eq "act") { print &get_lang_string("status") . ": " .  &get_lang_string("details") }
					elsif ($mode eq "bi") { print &get_lang_string("bi_head") . ": " .  &get_lang_string("details") }
					print " " .  &get_lang_string("for") . " " . $display->{$tree} . "</div>\n";
					print " 		<table id=\'nbp_table_tree\' class=\'status\'>\n";
					print " 			<tr>\n";
					print " 				<th> </th>\n";
					print " 				<th> </th>\n";
					print " 				<th class=\'status\'>" .  &get_lang_string("host") . "</th>\n";
					print " 				<th class=\'status\'>" .  &get_lang_string("service") . "</th>\n";
					print " 				<th class=\'status\'>" .  &get_lang_string("status") . "</th>\n";
					print " 				<th class=\'status\'>" .  &get_lang_string("status_information") . "</th>\n";
					print " 			</tr>\n";

					$rowcount=@services;
					for ($i=0; $i<@services; $i++)
					{
						$services[$i] = &cutOffSpaces($services[$i]);
						if ($i%2 == 0) { $rowclass = "statusEven" }
						else { $rowclass = "statusOdd" }
						print "			<tr>\n";
						if ($i == 0)
						{
							if ($operator eq "and" or $operator eq "or")
							{
								print "				<td rowspan=\'$rowcount\'><b>$operator</b><sup>*</sup></td>\n";
							}
							else
							{
								print "				<td rowspan=\'$rowcount\'><b>min $min_ok</b><sup>*</sup></td>\n";
							}
							#print "				<td rowspan=\"$rowcount\" bgcolor=\"black\" width=\"1\"> </td>\n";
							print "				<td rowspan=\"$rowcount\" id=\"nbp_curly_brace\"> </td>\n";
						}
						if ( $services[$i] =~ m/;/ )
						{
							# this output, if it is a single service
							($host, $service) = split(/;/, $services[$i]);
							$service_for_url = $service;
							$service_for_url =~ s/ /+/;
							if ($mode eq "act")
							{
								print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=1&amp;host=$host\">$host</a></td>\n";
								if ($service eq "Hoststatus")
								{
									print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=1&amp;host=$host\">$service</a></td>\n";
								}
								else
								{
									print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=2&amp;host=$host&amp;service=$service_for_url\">$service</a></td>\n";
								}
							}
							elsif ($mode eq "bi")
							{
								print "				<td class=\'$rowclass\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;detail=$detail&amp;tree=$tree&amp;lang=$lang&amp;trafficlight=$trafficlight&amp;disprio=$display_prio&amp;set=" . $cgi_simple->url_encode($host) . "\">$host</a></td>\n";
								print "				<td class=\'$rowclass\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;sessionid=$sessionid&amp;detail=$detail&amp;tree=$tree&amp;lang=$lang&amp;trafficlight=$trafficlight&amp;disprio=$display_prio&amp;set=" . $cgi_simple->url_encode("$host;$service") ."\">$service</a></td>\n";
							}
						
						}
						else
						{
							# this output, if it is an aggregated service
							print "				<td colspan=2 class=\'$rowclass\'><a href=\"$own_url?tree=$services[$i]&amp;trafficlight=$trafficlight&amp;conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;disprio=$display_prio\">$display->{$services[$i]}</a></td>\n";
						}
						print "				<td class=\'miniStatus$hardstates->{$services[$i]}\'>$hardstates->{$services[$i]}</td>\n";
						print "				<td class=\'$rowclass\'>$statusinfos->{$services[$i]}</td>\n";
						print "			</tr>\n";
					}
					print "			</table>\n";
					print "			<div id=\'nbp_hint\'>\n";
					if ($operator eq "and")
					{
						print "			<span class=\"nbp_text_small\"><sup>*</sup></span> <span class=\"nbp_text_tiny\">" .  &get_lang_string("hint_and") . "</span>\n";
					}
					elsif ($operator eq "of")
					{
						print "			<span class=\"nbp_text_small\"><sup>*</sup></span> <span class=\"nbp_text_tiny\">" .  &get_lang_string("hint_of", $min_ok) . "</span>\n";
					}
					else
					{
						print "			<span class=\"nbp_text_small\"><sup>*</sup></span> <span class=\"nbp_text_tiny\">" .  &get_lang_string("hint_or") . "</span>\n";
					}
					print "			</div>\n";
					print "			<div id=\'nbp_button_bar\'>\n";
					print "				<span id=\'nbp_back_button\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;trafficlight=$trafficlight&amp;disprio=$display_prio\">[" .  &get_lang_string("back_to_top") . "]</a></span>\n";
					print "			</div>\n";
					print "		</div>\n";
					&printPageFoot("html");
				}
				else
				{
					# Display tree view in json 
					# (only one level of hierarchy in the tree of one business process)

					&printPageHead("json");
					chomp($script_out->{$tree});
					my @tmp_array;
					
					# display_prio of the requested bp should be displayed in priority_definitions section of JSON output
					$used_priorities[$display_status->{$tree}] = 1;

					# print "tree:          $tree\n";
					# print "displayname:   $display->{$tree}\n";
					# print "components:    $components->{$tree}\n";
					# print "op:            $operator\n";
					# print "min_ok:        $min_ok\n" if (defined $min_ok);
					# print "external_info: $script_out->{$tree}\n" if (defined $script_out->{$tree});

					$json_data{'bp_id'}         = $tree;
					$json_data{"display_prio"}  = $display_status->{$tree};
					#if ($display_status->{$tree} != 0)
					#{
					#	$json_data{"display_prio_headline"}    = &get_lang_string("priority_" . $display_status->{$tree} . "_headline");
					#	$json_data{"display_prio_description"} = &get_lang_string("priority_" . $display_status->{$tree} . "_description");
					#}
					$json_data{"display_name"}  = $display->{$tree};
					$json_data{"hardstate"}     = $hardstates->{$tree};
					$json_data{"info_url"}      = $info_url->{$tree} if (defined $info_url->{$tree});
					$json_data{"external_info"} = $script_out->{$tree} if (defined $script_out->{$tree});
					$json_data{"operator"}      = $operator;
					$json_data{"min_ok"}        = $min_ok if (defined $min_ok);

					for ($i=0; $i<@services; $i++)
					{
						my %tmp_hash;

						# print "\n";
						$services[$i] = &cutOffSpaces($services[$i]);
						if ( $services[$i] =~ m/;/ )
						{
							# this output, if it is a single service
							($host, $service) = split(/;/, $services[$i]);
							# print "host:          $host\n";
							# print "service:       $service\n";
							$tmp_hash{"host"}     = $host;
							$tmp_hash{"service"}  = $service;
						}
						else
						{
							# this output, if it is an aggregated service
							# print "subprocess:    $services[$i]\n";
							# print "displayname:   $display->{$services[$i]}\n";
							# print "external_info: $script_out->{$services[$i]}\n" if (defined $script_out->{$services[$i]});

							$tmp_hash{"subprocess"}    = $services[$i];
							$tmp_hash{"display_prio"}  = $display_status->{$services[$i]};
							$tmp_hash{"display_name"}  = $display->{$services[$i]};
							$tmp_hash{"info_url"}      = $info_url->{$services[$i]} if (defined $info_url->{$services[$i]});
							$tmp_hash{"external_info"} = $script_out->{$services[$i]} if (defined $script_out->{$services[$i]});

							# display_prio of this sub process should be displayed in priority_definitions section of JSON output
							$used_priorities[$display_status->{$services[$i]}] = 1;
						}
						# print "hardstate:     $hardstates->{$services[$i]}\n";
						# print "statusinfo:    $statusinfos->{$services[$i]}\n" if (defined $statusinfos->{$services[$i]});

						$tmp_hash{"hardstate"}     = $hardstates->{$services[$i]};
						$tmp_hash{"plugin_output"} = $statusinfos->{$services[$i]} if (defined $statusinfos->{$services[$i]});

						push(@tmp_array, \%tmp_hash);
					}

					$json_data{"components"}    = \@tmp_array;
	
					$json{'business_process'} = \%json_data;
					$json{'priority_definitions'} = getPriorityDescriptions(@used_priorities);
					$json{'json_created'} = $timestamp;

					#print "\n\nDEBUG JSON:\n";
					$json_coder = JSON::XS->new->ascii->pretty->allow_nonref;
					print $json_coder->encode (\%json);
					print "\n";
					&printPageFoot("json");
				}
			}
		}
		else
		{
			# Display detail view (plain list without hierarchy)

			# check if the requested business process is defined 
			if ( ! defined $display->{$detail} )
			{
				&printPageHead("html", "norefresh");
				print "<div class=\'statusTitle\' id=\'nbp_error_head\'>" . &get_lang_string("error_bp_not_existing") . "</div>\n";
				print "<p id=\'nbp_error_text\'>\n";
				print &get_lang_string("error_bp_not_existing_body", $detail) . "\n";
				print "</p>\n";
				&printPageFoot("html");
				exit(0);
			}

			if ( $output_format eq "html" )
			{
				# Display detail view in HTML (plain list without hierarchy)

				&printPageHead("html");
				print "		<div id=\"nbp_single_table_box\">\n";
				print "		<div class=\'statusTitle\'>";
				if ($mode eq "act") { print &get_lang_string("status") . ": " .  &get_lang_string("details") }
				elsif ($mode eq "bi") { print &get_lang_string("bi_head") . ": " .  &get_lang_string("details") }
				print " " .  &get_lang_string("for") . " " . $display->{$detail} . "</div>\n";
				print " 		<table id=\'nbp_table_list\' class=\'status\'>\n";
				print " 			<tr>\n";
				print " 				<th class=\'status\'>" .  &get_lang_string("host") . "</th>\n";
				print " 				<th class=\'status\'>" .  &get_lang_string("service") . "</th>\n";
				print " 				<th class=\'status\'>" .  &get_lang_string("status") . "</th>\n";
				print " 				<th class=\'status\'>" .  &get_lang_string("status_information") . "</th>\n";
				print " 			</tr>\n";

				#print "Detail: $detail\n";
				@services = sort(&listAllComponentsOf($detail, $components));

				#print "<pre>\n";
				#printArray(\@services);
				#print "</pre>\n";

				$prev_host = "";
				for ($i=0; $i<@services; $i++)
				{
					#print "$services[$i] $hardstates{$services[$i]}\n";
					($host, $service) = split(/;/, $services[$i]);
					$service_for_url = $service;
					$service_for_url =~ s/ /+/;
					if ($i%2 == 0) { $rowclass = "statusEven" }
					else { $rowclass = "statusOdd" }
					print "			<tr class=\'$rowclass\'>\n";
					if ($prev_host eq $host)
					{
						print "				<td class=\'status\'>&nbsp;</td>\n";
					}
					else
					{
						if ($mode eq "act")
						{
							print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=1&amp;host=$host\">$host</a></td>\n";
						}
						elsif ($mode eq "bi")
						{
							print "				<td class=\'$rowclass\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;detail=$detail&amp;tree=$tree&amp;trafficlight=$trafficlight&amp;disprio=$display_prio&amp;set=" . $cgi_simple->url_encode($host) . "\">$host</a></td>\n";
						}
					}
					$prev_host = $host;
					if ($mode eq "act")
					{
						if ($service eq "Hoststatus")
						{
							print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=1&amp;host=$host\">$service</a></td>\n";
						}
						else
						{
							print "				<td class=\'$rowclass\'><a href=\"$settings->{'NAGIOS_CGI_URL'}/extinfo.cgi?type=2&amp;host=$host&amp;service=$service_for_url\">$service</a></td>\n";
						}
					}
					elsif ($mode eq "bi")
					{
						print "				<td class=\'$rowclass\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;detail=$detail&amp;tree=$tree&amp;trafficlight=$trafficlight&amp;disprio=$display_prio&amp;set=" . $cgi_simple->url_encode("$host;$service") . "\">$service</a></td>\n";
					}
					print "				<td class=\'miniStatus$hardstates->{$services[$i]}\'>$hardstates->{$services[$i]}</td>\n";
					print "				<td class=\'$rowclass\'>$statusinfos->{$services[$i]}</td>\n";
					print "			</tr>\n";
				}
	
				print "			</table>\n";
				print "			<div id=\'nbp_button_bar\'>\n";
				print "				<span id=\'nbp_back_button\'><a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;trafficlight=$trafficlight&amp;disprio=$display_prio\">[" .  &get_lang_string("back_to_top") . "]</a></span>\n";
				print "			</div>\n";
				print "		</div>\n";
				&printPageFoot("html");
			}
			else
			{
				# Display detail view in JSON (plain list without hierarchy)

				&printPageHead("json");
				my @tmp_array;
				#print "Detail: $detail\n";
				@services = sort(&listAllComponentsOf($detail, $components));
				chomp($script_out->{$detail});

				# printArray(\@services);
				# print "\n\n";
				# print "detail:        $detail\n";
				# print "displayname:   $display->{$detail}\n";
				# print "components:    $components->{$detail}\n";
				# print "external_info: $script_out->{$detail}\n" if (defined $script_out->{$detail});

				# display_prio of the requested bp should be displayed in priority_definitions section of JSON output
				$used_priorities[$display_status->{$detail}] = 1;

				$json_data{'bp_id'}         = $detail;
				$json_data{"display_prio"}  = $display_status->{$detail};
				if ($display_status->{$detail} != 0)
				{
					$json_data{"display_prio_headline"}    = &get_lang_string("priority_" . $display_status->{$detail} . "_headline");
					$json_data{"display_prio_description"} = &get_lang_string("priority_" . $display_status->{$detail} . "_description");
				}
				$json_data{"display_name"}  = $display->{$detail};
				$json_data{"hardstate"}     = $hardstates->{$detail};
				$json_data{"info_url"}      = $info_url->{$detail} if (defined $info_url->{$detail});
				$json_data{"external_info"} = $script_out->{$detail} if (defined $script_out->{$detail});

				for ($i=0; $i<@services; $i++)
				{
					my %tmp_hash;

					($host, $service) = split(/;/, $services[$i]);

					# print "host: $host\n";
					# print "service: $service\n";
					# print "hardstate: $hardstates->{$services[$i]}\n";
					# print "statusinfo: $statusinfos->{$services[$i]}\n";
					# print "\n";

					if ( $services[$i] =~ m/;/ )
					{
						# this output, if it is a single service
						($host, $service) = split(/;/, $services[$i]);
						# print "host:          $host\n";
						# print "service:       $service\n";
						$tmp_hash{"host"}     = $host;
						$tmp_hash{"service"}  = $service;
					}
					# print "hardstate:     $hardstates->{$services[$i]}\n";
					# print "statusinfo:    $statusinfos->{$services[$i]}\n" if (defined $statusinfos->{$services[$i]});
				
					$tmp_hash{"hardstate"}     = $hardstates->{$services[$i]};
					$tmp_hash{"plugin_output"} = $statusinfos->{$services[$i]} if (defined $statusinfos->{$services[$i]});
				
					push(@tmp_array, \%tmp_hash);
				}

				$json_data{"components"}    = \@tmp_array;

				$json{'business_process'} = \%json_data;
				$json{'priority_definitions'} = getPriorityDescriptions(@used_priorities);
				$json{'json_created'} = $timestamp;

				# print "\n\nDEBUG JSON:\n";
				$json_coder = JSON::XS->new->ascii->pretty->allow_nonref;
				print $json_coder->encode (\%json);
				print "\n";
				&printPageFoot("json");
			}
		}
	}




sub printPageHead()
{
	# as first parameter "pagetype" we get the string "html" or "json"
	# this is used to display errors in HTML even if the requested output type is JSON
	#
	# as second parameter give "refresh" or "norefresh"
	# (defaults to "refresh")
	# useful to prevent errorpages from refreshing
	my $pagetype = shift || "html";
	my $refresh = shift;
	$refresh = "refresh" if ($refresh ne "norefresh");

	if ($pagetype eq "html")
	{
	        print $query->header;
		if ( $trafficlight eq "short")
		{
			print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">' . "\n";
		}
		else
		{
			print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' . "\n";
		}
		print "<html>\n";
		print "	<head>\n";
		print "		<meta http-equiv=\"Content-type\" content=\"text/html;charset=ISO-8859-1\">\n";
		if ($mode eq "act") 
		{ 
			print "		<title>" .  &get_lang_string("bp_head") . "</title>\n";
		}
		elsif ($mode eq "bi") 
		{ 
			print "		<title>" .  &get_lang_string("bi_head") . "</title>\n";
		}

		print "		<link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'NAGIOS_BASE_URL'}/stylesheets/status.css\'>\n";
		print "		<link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'BP_ADDON_HTML_URL'}/stylesheets/nagios-bp.css\'>\n";
		print "		<link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'BP_ADDON_HTML_URL'}/stylesheets/user.css\'>\n";

		if ($mode eq "act" && $refresh eq "refresh") 
		{ 
			print "		<meta http-equiv=\"refresh\" content=\"60; URL=$own_url?detail=$detail&amp;tree=$tree&amp;lang=$lang&amp;conf=$conf&amp;trafficlight=$trafficlight\">\n";
		}

		if ($trafficlight eq "short")
		{
			print "		<base target=\"main\">\n";
			print "	</head>\n";
			print "	<body class=\'status\' id=\'nbp_body_short\'>\n";
		}
		else
		{
			print "	</head>\n";
			print "	<body class=\'status\' id=\'nbp_body_${mode}\'>\n";
		}
	}
	else
	{
		print "Content-Type: application/json\n\n";
	}
}

sub printPageFoot()
{
	# as first parameter "pagetype" we get the string "error" if an error page should be displayed
	# this is used to display errors in HTML even if the requested output type is JSON
	my $pagetype = shift || "html";

	if ( $pagetype eq "html" )
	{
		if ($trafficlight ne "short")
		{
			$languages = &getAvaiableLanguages();
			print "			<div id=\"nbp_foot\">\n";
			print "				<div id=\'nbp_foot_version\'>\n";
			print "					" . &get_lang_string("last_updated") . ": $timestamp<br>\n";
			print "					Nagios Business Process AddOn, " . &get_lang_string("version") . " " . &getVersion . "\n";
			print "				</div>\n";
			print "				<div id=\'nbp_foot_language\'>\n";
			print "				" . &get_lang_string("language") . ":\n";
			foreach $i (@$languages)
			{
				print "				<a href=\"$own_url?detail=$detail&amp;tree=$tree&amp;lang=$i&amp;conf=$conf&amp;mode=$mode&amp;trafficlight=$trafficlight&amp;disprio=$display_prio";
				# special handling for startpage BI
				if ( $new_session != 1)
				{
					print "&amp;sessionid=$sessionid";
				}
				print "\">$i</a>\n";
			}
			print "				</div>\n";
			print "			</div>\n";
		}
		print "	</body>\n";
		print "</html>\n";
	}
}

sub displayPrio()
{
	my $prio = shift;

	print " 			<tr>\n";
	print "					<td colspan=\"5\" class=\'statusTitle\'>" .  &get_lang_string("priority_" . $prio . "_headline") . "</td>\n";
	print " 			</tr>\n";
	print " 			<tr>\n";
	print "					<td colspan=\"5\" class=\"nbp_description\">" .  &get_lang_string("priority_" . $prio . "_description") . "</td>\n";
	print " 			</tr>\n";
	print " 			<tr>\n";
	print " 				<th class=\'status\'>" .  &get_lang_string("business_process") . "</th>\n";
	print " 				<th class=\'status\'>&nbsp;</th>\n";
	print " 				<th class=\'status\'>" .  &get_lang_string("status") . "</th>\n";
	print " 				<th class=\'status\'>&nbsp;</th>\n";
	print " 				<th class=\'status\'>" .  &get_lang_string("status_information") . "</th>\n";
	print " 			</tr>\n";

	foreach $key (sort keys %$display)
	{
		if ($display_status->{$key} == $prio)
		{
			#print "$key $display->{$key}\n";
			$rowcount = ($rowcount + 1)%2;
			if ($rowcount == 0) { $rowclass = "statusEven" }
			else { $rowclass = "statusOdd" }
			print "			<tr class=\'$rowclass\'>\n";
			print "				<td class=\'$rowclass\'><a href=\"$own_url?detail=$key&amp;conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;trafficlight=$trafficlight&amp;disprio=$display_prio\">$display->{$key}</a></td>\n";
			print "				<td class=\'$rowclass\'><a href=\"$own_url?tree=$key&amp;conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;sessionid=$sessionid&amp;trafficlight=$trafficlight&amp;disprio=$display_prio\"><img class=\"nbp_no_border\" src=\"$settings->{'BP_ADDON_HTML_URL'}/tree.gif\" height=\"20\" alt=\"" .  &get_lang_string("tree_view") . "\" title=\"" .  &get_lang_string("tree_view") . "\"></a></td>\n";
			print "				<td class=\'miniStatus$hardstates->{$key}\'>$hardstates->{$key}</td>\n";
			print "				<td class=\'$rowclass\'>";
			if ($info_url->{$key} ne "")
			{
				print "<a href=\"$info_url->{$key}\"><img class=\"nbp_no_border\" src=\"$settings->{'BP_ADDON_HTML_URL'}/info4.gif\" alt=\"" .  &get_lang_string("info") . "\" title=\"" .  &get_lang_string("info") . "\"></a>";
			}
			print "</td>\n";
			print "				<td class=\'$rowclass\'>$script_out->{$key}</td>\n";
			print "			</tr>\n";
		}
	}
	print " 			<tr>\n";
	print "					<td class=\"nbp_central_table_spacer\" colspan=\"5\"></td>\n";
	print " 			</tr>\n";
}

sub loadSession()
{
	my $session_file = shift;
	$session_file = "$session_dir/$session_file";

	if ( ! -f $session_file )
	{
		&printPageHead("html");
		print "<div class=\'statusTitle\' id=\'nbp_error_head\'>" .  &get_lang_string("error_not_existing_session_head") . "</div>\n";
		print "<p id=\'nbp_error_text\'>\n";
		print "		" .  &get_lang_string("error_not_existing_session_body") . "\n";
		print "</p>\n";
		print "<div id=\'nbp_button_bar\'>\n";
		print "	<a href=\"$own_url?conf=$conf&amp;mode=$mode&amp;lang=$lang&amp;trafficlight=$trafficlight&amp;disprio=$display_prio\">[" .  &get_lang_string("bi_start_session") . "]</a>\n";
		print "</div>\n";
		&printPageFoot();
	}

	open(IN, "<$session_file") or die "unable to read session information from $session_file\n";
		while ($in = <IN>)
		{
			chomp($in);
			$in =~ m/^([a-z]+):([^=]+)=(.+)/;
			#print "$1 xxx $2 xxx $3 <br>\n";
			if ($1 eq "hardstates") { $hardstates->{$2} = $3 };
			if ($1 eq "statusinfos") { $statusinfos->{$2} = $3 };
		}
	close(IN);
}

sub saveSession()
{
	my $session_file = shift;
	$session_file = "$session_dir/$session_file";

	open(OUT, ">$session_file") or die "unable to persist session to $session_file\n";
		foreach $key (keys %$hardstates)
		{
			print OUT "hardstates:$key=$hardstates->{$key}\n";
			print OUT "statusinfos:$key=$statusinfos->{$key}\n";
		}
	close(OUT);
}

sub getPriorityDescriptions()
{
	my @requested_prios = @_;
	my %prio_def;

	for ($prio=1; $prio<=@requested_prios; $prio++)
	{
		my %tmp_hash;
		if (defined $requested_prios[$prio])
		{
			$tmp_hash{"display_prio_headline"}    = &get_lang_string("priority_${prio}_headline");
			$tmp_hash{"display_prio_description"} = &get_lang_string("priority_${prio}_description");
			$prio_def{$prio} = \%tmp_hash;
		}
	}

	return(\%prio_def);
}
