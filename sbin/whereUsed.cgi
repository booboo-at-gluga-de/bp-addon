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

#some Variables
        my $settings = getSettings();
        # where is the cgi.cfg file located?
        # from this we take the credentials and location of the database
        my $nagios_bp_conf = $settings->{'BP_ADDON_ETC'} . "/";
	my $default_language = "de";
	my $own_url = $ENV{"SCRIPT_NAME"};
        my $cgi_simple = new CGI::Simple;       #Instance of CGI simple
        my $query = new CGI;                    #Instance of CGI module
	my ($display, $display_status, $script_out, $info_url, $components, $hardstates, $statusinfos, $key, @component_list, @match, @object_stack, $rowcount, $rowclass, $infostring, $i);

        # which configfile do we work on
        my $conf = $query->param("conf");
	# lang can be used if you want to use a dedicated language, not the language submitted in Accept Language Header
        my $lang = $query->param("lang");
	# the host You want to know about
        my $host = $query->param("host");
	# the service You want to know about
        my $service = $query->param("service");

#set defaults
        if ($conf eq "" || $conf !~ m/^[a-zA-Z0-9_\-]+$/ ) { $conf = "business-processes" }
        $nagios_bp_conf .= $conf . ".conf";

        if ($service !~ m/^[a-zA-Z0-9_\-\+\.\/ ]+$/ || $service =~ m/\.\./ ) { $service = "" }
        if ($host !~ m/^[a-zA-Z0-9_\-\+\.\/ ]+$/ || $host =~ m/\.\./ ) { $host = "" }
	
	# try to guess the host and service from the referer
	if ($service eq "" && $host eq "" && $ENV{'HTTP_REFERER'} ne "")
	{
		#print "HTTP_REFERER: $ENV{'HTTP_REFERER'}<br>\n";
		if ($ENV{'HTTP_REFERER'} =~ m/host=([^&]+)/)
		{
			#$host = $1;
			$host = $cgi_simple->url_decode($1);
        		if ($host !~ m/^[a-zA-Z0-9_\-\+\. ]+$/ || $host =~ m/\.\./ ) { $host = "" }
		}
		if ($ENV{'HTTP_REFERER'} =~ m/service=([^&]+)/)
		{
			#$service = $1;
			$service = $cgi_simple->url_decode($1);
        		if ($service !~ m/^[a-zA-Z0-9_\-\+\. ]+$/ || $service =~ m/\.\./ ) { $service = "" }
			#$service =~ s/\+/ /g;
			#$service =~ s/%20/ /g;
		}
	}

	$service =~ s/^\s+//;
	$service =~ s/\s+$//;
	$host =~ s/^\s+//;
	$host =~ s/\s+$//;

	#print "host: \"$host\"<br>\n";
	#print "service: \"$service\"<br><br>\n";

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
                &printPageHead();
                print "<div class=\'statusTitle\' id=\'bpa_error_head\'>" . &get_lang_string("error_wrong_parameter_conf_head") . "</div>\n";
                print "<P id=\'bpa_error_text\'>\n";
                print &get_lang_string("error_wrong_parameter_conf_body", $nagios_bp_conf) . "\n";
                print "</P>\n";
                &printPageFoot();
		exit;
        }
	# parameter host
        if ( $host eq "" )
        {
                &printPageHead();
                print "<div class=\'statusTitle\' id=\'bpa_error_head\'>" . &get_lang_string("error_wrong_parameter_host_head") . "</div>\n";
                print "<P id=\'bpa_error_text\'>\n";
                print &get_lang_string("error_wrong_parameter_host_body") . "\n";
                print "</P>\n";
                &printPageFoot();
		exit;
        }


# generate output page
	&printPageHead();
	print "         <div id=\'bpa_toplevel_box\'>\n";
	# right bar
	displayRightBar();
	print "         <div id=\"bpa_cental_table_box_tl_yes\">\n";
	print "		<div class=\'statusTitle\' id=\'bpa_head_wu\'>" . &get_lang_string("where_used_body") . "</div>\n";

	($hardstates, $statusinfos) = &getStates();
	($display, $display_status, $script_out, $info_url, $components) = &getBPs($nagios_bp_conf, $hardstates);

	if ($service eq "")
	{
		output("$host;.+", &get_lang_string("host") . " \"$host\"", "host");
	}
	else
	{
		output("$host;$service", &get_lang_string("service_on_host", $service, $host), "service");
		output("$host;.+", &get_lang_string("host") . " \"$host\"", "host");
	}
	print "		</div>\n";
	print "		</div>\n";
	&printPageFoot();


# subroutines

#############################################################################
sub output()
#############################################################################
{
	my $searchfor = shift;
	my $display_string = shift;
	my $object_type = shift;
	my $last;
	my @resultset = ();

	#printBPs($searchfor);
	#
	#while (@object_stack > 0)
	#{
	#	print "\nDEBUG: object_stack is now:\n";
	#	printArray(\@object_stack);
	#
	#	printBPs(shift @object_stack);
	#}

	#print "DEBUG searchfor: $searchfor\n";
	foreach $key (keys %$display)
	{
		@match = grep(/^$searchfor$/, &listAllComponentsOf($key, $components));
		if (@match > 0 && $display_status->{$key} > 0)
		{
			#print "DEBUG: BP $key contains: " . join(", ", &listAllComponentsOf($key, $components)) . "\n";
			push(@resultset, $key);
			#print "DEBUG: resultset len " . @resultset . "\n";
		}
	}

	if (@resultset == 0)
	{
		print "<div class=\'statusTitle\' id=\'bpa_wu_${object_type}_head\'>" . &get_lang_string('not_used_anywhere', $display_string) . "</div>\n";
	}
	else
	{
		$rowcount=0;
		print "<div class=\'statusTitle\' id=\'bpa_wu_${object_type}_head\'>" . &get_lang_string('used_in_these_bps', $display_string) . ":</div>\n";
		print "<div id=\'bpa_wu_${object_type}_box\'>\n";
		print "    <table class='status' id=\'bpa_wu_${object_type}_table\'>\n";
		print "		<tr>\n";
		print "			<th class='status'>" . &get_lang_string('business_process') . "</th>\n";
		print "			<th class='status'>&nbsp;</th>\n";
		print "			<th class='status'>" . &get_lang_string('status') . "</th>\n";
		print "			<th class='status'>&nbsp;</th>\n";
		print "		</tr>\n";

		foreach $key (sort @resultset)
		{
			if ($last ne $key)
			{
				$rowcount = ($rowcount + 1)%2;
				if ($rowcount == 0) { $rowclass = "statusEven" }
				else { $rowclass = "statusOdd" }

				if ($info_url->{$key} ne "")
				{
					$infostring = "<a href=\"$info_url->{$key}\"><img class=\"bpa_no_border\" src=\"" . $settings->{'BP_ADDON_HTML_URL'} . "/info4.gif\" alt=\"" .  &get_lang_string("info") . "\" title=\"" .  &get_lang_string("info") . "\"></a>";
				}
				else
				{
					$infostring = "";
				}

				print "	<tr class='$rowclass'>\n";
				print "		<td class=\'$rowclass\'><a href=\"$settings->{'BP_ADDON_CGI_URL'}/bp-addon.cgi?detail=$key&amp;mode=act&amp;conf=$conf\">$display->{$key}</a> - " . &get_lang_string('prio') . " $display_status->{$key}</td>\n";
				print "		<td class=\'$rowclass\'><a href=\"$settings->{'BP_ADDON_CGI_URL'}/bp-addon.cgi?tree=$key&amp;ode=act&amp;conf=$conf\"><img class=\"bpa_no_border\" src=\"$settings->{'BP_ADDON_HTML_URL'}/tree.gif\" height=\"20\" alt=\"" . &get_lang_string('tree_view') . "\" title=\"" . &get_lang_string('tree_view') . "\"></a></td>\n";
				print "		<td class=\'miniStatus$hardstates->{$key}\'>$hardstates->{$key}</td>\n";
				print "		<td class=\'$rowclass\'>$infostring</td>\n";
				print "	</tr>\n";
			}
			$last = $key;
		}
		print "</table>\n";
		print "</div>\n";
	}
}

#############################################################################
sub printPageHead()
#############################################################################
{
        print $query->header;
	print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' . "\n";
        print "<html>\n";
        print " <head>\n";
	print "         <meta http-equiv=\"Content-type\" content=\"text/html;charset=ISO-8859-1\">\n";
        print "         <title>" .  &get_lang_string("where_used_head") . "</title>\n";
        print "         <link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'NAGIOS_BASE_URL'}/stylesheets/status.css\'>\n";
        print "         <link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'BP_ADDON_HTML_URL'}/stylesheets/bp-addon.css\'>\n";
        print "         <link rel=\'stylesheet\' type=\'text/css\' href=\'$settings->{'BP_ADDON_HTML_URL'}/stylesheets/user.css\'>\n";
        print " </head>\n";
        print " <body class=\'status\' id=\'bpa_body_wu\'>\n";
}

#############################################################################
sub printPageFoot()
#############################################################################
{
        print " </body>\n";
        print "</html>\n";
}


#############################################################################
sub displayRightBar()
#############################################################################
{
	# display the right bar
	my $languages = &getAvaiableLanguages();
	my $timestamp = getCurrentTimestamp();

	print "			<div id=\"bpa_right_bar\">\n";
	print "			<a href=\"http://bp-addon.monitoringexchange.org\"><img class=\"bpa_logo\" src=\"$settings->{'BP_ADDON_HTML_URL'}/bp-logo_150.png\" height=\"109\" width=\"150\" alt=\"Business Process AddOn for Nagios and Icinga\" title=\"Business Process AddOn for Nagios and Icinga\"></a>\n";

	# language selection in right bar
	print "				<div id=\'bpa_language\'>\n";
	print "				" . &get_lang_string("language") . ":\n";
        foreach $i (@$languages)
        {
		print "				<a href=\"$own_url?host=$host&amp;service=$service&amp;lang=$i&amp;conf=$conf\">$i</a> \n";
        }
	print "				</div>\n";

	# page creation timestamp
	print "				<div id=\'bpa_last_updated\'>" . &get_lang_string("last_updated") . ":<br> $timestamp<br></div>\n";

	# version in right bar
	print "				<div id=\'bpa_version\'>Business Process AddOn, <br>" . &get_lang_string("version") . " " . &getVersion . "</div>\n";

	# end bpa_right_bar
	print " 			</div>\n";
}
