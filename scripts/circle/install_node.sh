#!/bin/bash
set -ev
if [ $NODE_VERSION ]
then
  curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh | bash
  source ~/.nvm/nvm.sh
  nvm install $NODE_VERSION
  nvm use $NODE_VERSION
  npm install -g bower
  npm install
  bower install
fi
