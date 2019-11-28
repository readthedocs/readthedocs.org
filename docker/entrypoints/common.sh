#! /bin/sh

# This file is useful when you need to run a command on all the Python
# instances and you don't want to rebuild the image. For example, when
# working on a feature that requires a new dependency and you need to
# call: "pip install newdependency==1.4.2". You can add that command
# here, and it will be executed in all the instances at startup.
