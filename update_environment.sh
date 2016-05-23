#!/bin/bash

set -x

# Some commands that help us get in the right docker situation.

# Work has me on docker171, so we unlink that
brew unlink docker171
# Begin work on the latest docker
brew link docker
# What machines are running?
docker-machine ls
# Start the machine
docker-machine start wikinetwork
# Set up our environment
eval "$(docker-machine env wikinetwork)"
# What are we working with here?
docker ps
