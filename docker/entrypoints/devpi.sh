#! /bin/sh


pip3 install devpi-server
devpi-init --serverdir=/devpi
devpi-server --host=0.0.0.0 --absolute-urls --serverdir=/devpi
