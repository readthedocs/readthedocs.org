#!/bin/bash
set -ev
if [ $NODE_VERSION ]
then
  git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.11.3
  . "$HOME/.asdf/asdf.sh"
  asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
  asdf install nodejs $NODE_VERSION
  asdf global nodejs $NODE_VERSION
  npm install -g bower
  npm install
  bower install
fi
