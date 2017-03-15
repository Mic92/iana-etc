#!/usr/bin/env bash

set -eux # Exit with nonzero exit code if anything fails

# Pull requests and commits to other branches shouldn't try to deploy, just build to verify
if [[ "$TRAVIS_PULL_REQUEST" != "false" ]] || \
	[[ "$TRAVIS_BRANCH" != master ]] && \
	[[ "$TRAVIS_BRANCH" != "$(cat .version)" ]]; then
    echo "Skipping deploy; just doing a build."
    python update.py out
    exit 0
fi

git clone "git@github.com:Mic92/iana-etc.git" out
(
  cd out 
  git checkout iana-numbers || git checkout --orphan iana-numbers
)

# Clean out existing contents
rm -rf out/**/* || exit 0

python ~/iana-etc/update.py out
cp -r out/dist "$TRAVIS_BUILD_DIR"

if [ "$TRAVIS_BRANCH" = master ]; then
    cd out
    git config user.name "Travis CI"
    git config user.email "$COMMIT_AUTHOR_EMAIL"
    
    if [ -z "$(git diff --exit-code)" ]; then
    	echo "No changes to the output on this push; exiting."
    	exit 0
    fi
    
    git add .
    git commit -m "add new iana release $(cat .version)"
    # release already exists
    git tag "$(cat .version)" || exit 0
    
    git push --tags origin iana-numbers
fi
