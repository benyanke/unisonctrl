#!/usr/bin/env bash

# Run this script on first set up, it installs git commit hooks.

export GIT_DIR="$(git rev-parse --show-toplevel)/.git"

$GIT_DIR/../git-misc/updateHooks.sh

echo "First time set up correctly configured. Your git hooks will now be managed in the repository.";
