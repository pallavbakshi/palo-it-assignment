#!/bin/bash

# Not using this script because it's not worth it.

# Sometimes black introduces a lot of noise because version upgrade.
# This script runs black on the files before they were changed by
# the user. Then it commits those changes made by black on the
# original file.
# This way we ensure all the noise by black is separated from the
# code written by the user.

echo "============ Running ⚫️ black on original files changed by the user ============"

# Following files have been modified
filesChanged=$(git ls-files -m | tr '\n' ' ')

echo "Following files have been modified by the user: $filesChanged"
echo "Running black on these files before the modifications made by the user"

# Stashing the changes made by user
echo "git stash"
git stash

# Running black on the files modified by user
black $filesChanged
filesChangedByBlack=$(git ls-files -m | tr '\n' ' ')

# If files were modified by black then committing them
if [ -z "$filesChangedByBlack" ]
  then
    echo "No files were changed by black. Aborting 🛑"
  else
    echo "Following were changed by black: $filesChangedByBlack"
    git add filesChangedByBlack
    git commit -m "Reformat Files"
fi

# Applying back the changes by user
echo "git stash apply 0"
git stash apply 0