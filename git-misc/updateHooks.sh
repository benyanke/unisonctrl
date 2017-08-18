#!/bin/bash


# This script runs on most git actions. It updates the git hooks directory to
# keep it in sync with the repo.

# Note: this script can not be called directly, and must be called from a git hook.

if [ -z ${GIT_DIR+x} ] ; then
  echo "'\$GIT_DIR' isn't set. Note: don't call this script directly, it is called by other scripts only.";
  exit 1;
fi

# Find git root
gitRoot="$(cd "$GIT_DIR/../"; pwd;)";

echo $gitroot;

# Copy git hooks from repo into git directory to keep them up to date
rm "$gitRoot/.git/hooks/"* -rf > /dev/null

# Copy global hooks
cp -a "$gitRoot/git-misc/git-hooks/"* "$gitRoot/.git/hooks/" > /dev/null


# Copy user-specific hooks, if they exist
if [[ -d "$gitRoot/git-misc/git-hooks-nosync/" ]] && [[ "$(ls -A $gitRoot'/git-misc/git-hooks-nosync/')" ]] ; then

  cp -a "$gitRoot/git-misc/git-hooks-nosync/"* "$gitRoot/.git/hooks/" > /dev/null
fi

# Set all hooks to executable
chmod +x "$gitRoot/.git/hooks/"* > /dev/null
