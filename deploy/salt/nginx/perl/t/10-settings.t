use Test::More;
use ReadTheDocs;

plan tests => 6;

no strict 'refs';
no warnings 'redefine';


our $Metadata_JSON = {};
$Metadata_JSON->{'/tmp/foo'} = qq/
{"name": "foo-name", "version": "foo-version"}
/;
$Metadata_JSON->{'/tmp/bar'} = qq/
{"name": "bar-name", "nothing": "something"}
/;
$Metadata_JSON->{'/tmp/fail'} = qq/
{"name": "fail", non of this matters}
/;

{
    local *ReadTheDocs::project_metadata_read = sub {
        my $file = shift;
        return $Metadata_JSON->{$file};
    };

    my $metadata = ReadTheDocs::project_metadata('/tmp/foo');
    is($metadata->{name}, 'foo-name');
    is($metadata->{version}, 'foo-version');
    undef $metadata;

    my $metadata = ReadTheDocs::project_metadata('/tmp/bar');
    is($metadata->{name}, 'bar-name');
    is($metadata->{version}, undef);
    undef $metadata;

    my $metadata = ReadTheDocs::project_metadata('/tmp/test');
    is($metadata->{name}, undef);
    is($metadata->{version}, undef);
    undef $metadata;
}

1;
