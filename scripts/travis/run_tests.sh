if ! [[ "$TOXENV" =~ ^(docs|lint|eslint) ]];
then
    args="'--including-search'"
fi
tox $args
