if ! [[ "$TOXENV" =~ ^(docs|lint|eslint|migrations) ]];
then
    args="--including-search"
fi
tox -- $args
