package ReadTheDocs;

use strict;
use warnings;

use JSON qw//;
use I18N::AcceptLanguage;


=head2 redirect_home

Redirect project subdomain home to correct build path, bypassing Django. This
requires the project have a C<metadata.json> that is updated when a project is
built or settings are saved. The metadata can include the following keys:

=over

=item version

Default project version, will default to C<latest>

=item language

Default project language, will default to C<en>

=item languages

Languages from linked translation projects. The default language will be added
to this list as the primary language. A lookup on the C<Accept-Language> header
will redirect to the correct language page, as long as there is a translation
for the project.

=back

Inside the Nginx config, the variable C<rtd_metadata> should be set to the path
of the C<metadata.json> path:

    location ~ /$ {
        set $rtd_metadata /home/docs/sites/readthedocs.org/checkouts/readthedocs.org/user_builds/$domain/metadata.json;
        perl ReadTheDocs::redirect_home;
    }


=cut

sub redirect_home {
    my $req = shift;
    my $version = 'latest';
    my $lang = 'en';

    my $metadata_file = $req->variable('rtd_metadata');
    if (defined $metadata_file) {
        my $metadata = project_metadata($metadata_file);

        # Version
        $version = $metadata->{version} || 'latest';

        # Language, add default as the primary language
        $lang = $metadata->{language} || 'en';
        my $languages = $metadata->{languages};
        unshift(@{$languages}, $lang);

        my $header = $req->header_in('Accept-Language');
        my $accept = I18N::AcceptLanguage->new();
        $accept->defaultLanguage($lang);
        $lang = $accept->accepts($header, $languages);
    }

    # Return redirect, no body
    $req->header_out('Location', sprintf('/%s/%s/', $lang, $version));
    $req->header_out('X-Perl-Redirect', 'True');
    return 302;
}

=head2 project_metadata($project)

Return parsed metadata from JSON metadata file

=cut

sub project_metadata {
    my $filename = shift;
    my $file = project_metadata_read($filename);
    my $metadata = {};
    eval {
        $metadata = JSON->new->utf8->decode($file);
    };
    return $metadata;
}

sub project_metadata_read {
    my $filename = shift;
    my $file = "";
    if (-e $filename) {
        open(my $fh, '<', $filename);
        $file = <$fh>;
    }
    return $file;
}

1;
