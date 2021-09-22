#!/usr/bin/env bash

set -eux # Exit with nonzero exit code if anything fails

# Clean out existing contents
rm -rf out/**/* || exit 0

python3 ~/iana-etc/update.py out

cd out

if [ -z "$(git diff --exit-code)" ]; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

find out

git add --all .
git commit -m "add new iana release $(cat .version)"
git push origin iana-numbers

tag=$(cat .version)
gh release delete "$tag" </dev/null || true
gh release create --title "$tag" "$tag" out/dist/* </dev/null
