use Test::More;
use ReadTheDocs;

plan tests => 46;

no strict 'refs';
no warnings 'redefine';


our $Metadata_Fixture = {
    '/tmp/foobar' => {
        name => 'foobar',
        version => '1.1',
        languages => ['es', 'en', 'fr']
    },
    '/tmp/test' => {
        name => 'test',
        version => '2.2',
        language => 'es',
        languages => ['fr', 'ru']
    },
    '/tmp/lang' => {
        name => 'lang',
        version => '3.3',
        language => 'ru',
        languages => ['en']
    }
};

{
    package ReadTheDocs::Request;

    sub new {
        my $class = shift;
        my %args = @_;
        bless {
            %args,
            output => []
        }, $class;
    }

    sub variable {
        my $self = shift;
        my $name = shift;
        return $self->{variable}->{$name};
    }

    sub header_in {
        my $self = shift;
        my $name = shift;
        return $self->{header}->{$name};
    }

    sub header_out {
        my ($self, $name, $value) = @_;
        push(@{$self->{output}}, sprintf("%s: %s", $name, $value)); 
    }

    sub send_http_header {
        my $self = shift;
        return;
    }

    sub print {
        my $self = shift;
        push(@{$self->{output}}, shift); 
    }
}

{
    local *ReadTheDocs::project_metadata = sub {
        my $file = shift;
        return $Metadata_Fixture->{$file};
    };

    # Test metadata
    my $metadata = ReadTheDocs::project_metadata('/tmp/foobar');
    is($metadata->{name}, 'foobar');
    is($metadata->{version}, '1.1');

    # Mock redirection for project 'foobar'
    my $test_cb = sub {
        my ($lang, $metadata, $url) = @_;
        my $req = ReadTheDocs::Request->new(
            variable => {rtd_metadata => $metadata},
            header => {'Accept-Language' => $lang}
        );
        is(ReadTheDocs::redirect_home($req), 302);
        is(
            pop(@{$req->{output}}),
            sprintf('Location: %s', $url),
            sprintf('Testing %s -> %s', $metadata, $url)
        );
    };

    # Languages: ['es', 'en', 'fr']
    $test_cb->('es,en', '/tmp/foobar', '/es/1.1/');
    $test_cb->('du', '/tmp/foobar', '/en/1.1/');
    $test_cb->('en;q=0.8, es', '/tmp/foobar', '/es/1.1/');
    $test_cb->('ru', '/tmp/foobar', '/en/1.1/');
    $test_cb->('en-gb;q=0.8, en;q=0.7, da', '/tmp/foobar', '/en/1.1/');

    # Languages: ['es', 'fr', 'ru']
    $test_cb->('es,en', '/tmp/test', '/es/2.2/');
    $test_cb->('du', '/tmp/test', '/es/2.2/');
    $test_cb->('en;q=0.8, es', '/tmp/test', '/es/2.2/');
    $test_cb->('ru', '/tmp/test', '/ru/2.2/');
    $test_cb->('en-gb;q=0.8, en;q=0.7, da', '/tmp/test', '/es/2.2/');

    # Languages: ['ru', 'en']
    $test_cb->('es,en', '/tmp/lang', '/en/3.3/');
    $test_cb->('du', '/tmp/lang', '/ru/3.3/');
    $test_cb->('en;q=0.8, es', '/tmp/lang', '/en/3.3/');
    $test_cb->('ru', '/tmp/lang', '/ru/3.3/');
    $test_cb->('ru', '/tmp/lang', '/ru/3.3/');
    $test_cb->('en-gb;q=0.8, en;q=0.7, da', '/tmp/lang', '/en/3.3/');

    # Languages: ['en']
    $test_cb->('es,en', '/tmp/nonexistant', '/en/latest/');
    $test_cb->('du', '/tmp/nonexistant', '/en/latest/');
    $test_cb->('en;q=0.8, es', '/tmp/nonexistant', '/en/latest/');
    $test_cb->('ru', '/tmp/nonexistant', '/en/latest/');
    $test_cb->('ru', '/tmp/nonexistant', '/en/latest/');
    $test_cb->('en-gb;q=0.8, en;q=0.7, da', '/tmp/nonexistant', '/en/latest/');
}

1;
