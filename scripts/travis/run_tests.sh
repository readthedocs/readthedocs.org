if ! [[ "$TOXENV" =~ ^(docs|docs-linkcheck|lint|eslint|migrations) ]];
then
    args="--including-search"
fi
tox -- $args
