#!/usr/bin/env bash

set -eux # Exit with nonzero exit code if anything fails

# Pull requests and commits to other branches shouldn't try to deploy, just build to verify
if [[ "$TRAVIS_PULL_REQUEST" != "false" ]] || \
	[[ "$TRAVIS_BRANCH" != master ]] && \
	[[ "$TRAVIS_BRANCH" != iana-numbers ]]; then
    echo "Skipping deploy; just doing a build."
    python update.py out
    exit 0
fi

# Clone the existing gh-pages for this repo into out/
# Create a new empty branch if gh-pages doesn't exist yet (should only happen on first deply)
git clone "$REPO" out
(
  cd out 
  git checkout iana-numbers || git checkout --orphan iana-numbers
)

# Clean out existing contents
rm -rf out/**/* || exit 0

git show MASTER:update.py > /tmp/update.py

python /tmp/update.py out

if [ "$TRAVIS_BRANCH" = master ]; then
    cd out
    git config user.name "Travis CI"
    git config user.email "$COMMIT_AUTHOR_EMAIL"
    
    if [ -z "$(git diff --exit-code)" ]; then
    	echo "No changes to the output on this push; exiting."
    	exit 0
    fi
    
    git add .
    git commit -m "New to GitHub Pages: ${SHA}"
    git tag "$(cat out/.version)"
    
    ENCRYPTED_KEY_VAR="encrypted_${ENCRYPTION_LABEL}_key"
    ENCRYPTED_IV_VAR="encrypted_${ENCRYPTION_LABEL}_iv"
    ENCRYPTED_KEY=${!ENCRYPTED_KEY_VAR}
    ENCRYPTED_IV=${!ENCRYPTED_IV_VAR}
    openssl aes-256-cbc \
	    -K "$ENCRYPTED_KEY" \
	    -iv "$ENCRYPTED_IV" \
	    -in deploy_key.enc \
	    -out deploy_key \
	    -d
    chmod 600 deploy_key
    eval "$(ssh-agent -s)"
    ssh-add deploy_key
    
    git push "$SSH_REPO" iana-numbers
elif [ "$TRAVIS_BRANCH" = iana-numbers ]; then
    cp out/dist ..
fi
