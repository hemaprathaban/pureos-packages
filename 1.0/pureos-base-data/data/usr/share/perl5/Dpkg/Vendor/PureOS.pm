# Copyright © 210 Ruben Rodriguez <ruben@pureos.info>
# Copyright © 2009 Raphaël Hertzog <hertzog@debian.org>
# Copyright © 2008 Ian Jackson <ian@davenant.greenend.org.uk>, Colin Watson
# <cjwatson@ubuntu.com>, James Westby <jw+debian@jameswestby.net>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

package Dpkg::Vendor::PureOS;

use strict;
use warnings;

use Dpkg::ErrorHandling;
use Dpkg::Gettext;

use base 'Dpkg::Vendor::Debian';

=head1 NAME

Dpkg::Vendor::PureOS - PureOS vendor object

=head1 DESCRIPTION

This vendor object customize the behaviour of dpkg-source
to check that Maintainers have been modified if necessary.

=cut

sub run_hook {
    my ($self, $hook, @params) = @_;

    if ($hook eq "before-source-build") {
        my $src = shift @params;
        my $fields = $src->{'fields'};

        # check that Maintainer/XSBC-Original-Maintainer comply to
        # https://wiki.ubuntu.com/DebianMaintainerField
        if (defined($fields->{'Version'}) and defined($fields->{'Maintainer'}) and
           $fields->{'Version'} =~ /pureos/) {
           if ($fields->{'Maintainer'} !~ /pureos/i) {
               if (defined ($ENV{'DEBEMAIL'}) and $ENV{'DEBEMAIL'} =~ /\@pureos\.info/) {
                   error(_g('Version number suggests PureOS changes, but Maintainer: does not have PureOS address'));
               } else {
                   warning(_g('Version number suggests PureOS changes, but Maintainer: does not have PureOS address'));
               }
           }
           unless ($fields->{'Original-Maintainer'}) {
               warning(_g('Version number suggests PureOS changes, but there is no XSBC-Original-Maintainer field'));
           }
        }

    } elsif ($hook eq "before-changes-creation") {
        my $fields = shift @params;

        # Add Launchpad-Bugs-Fixed field
        my $bugs = find_launchpad_closes($fields->{"Changes"} || "");
        if (scalar(@{$bugs})) {
            $fields->{"Launchpad-Bugs-Fixed"} = join(" ", @{$bugs});
        }

    } elsif ($hook eq "keyrings") {
        my @keyrings = $self->SUPER::run_hook($hook);

        push(@keyrings, '/usr/share/keyrings/pureos-archive-keyring.gpg');
        return @keyrings;
    }
}

=head1 PUBLIC FUNCTIONS

=over

=item $bugs = Dpkg::Vendor::PureOS::find_launchpad_closes($changes)

Takes one string as argument and finds "LP: #123456, #654321" statements,
which are references to bugs on Launchpad. Returns all closed bug
numbers in an array reference.

=cut

sub find_launchpad_closes {
    my ($changes) = @_;
    my @closes = ();

    while ($changes &&
          ($changes =~ /lp:\s+\#\d+(?:,\s*\#\d+)*/ig)) {
       push(@closes, $& =~ /\#?\s?(\d+)/g);
    }

    @closes = sort { $a <=> $b } @closes;

    return \@closes;
}

=back

=cut

1;
