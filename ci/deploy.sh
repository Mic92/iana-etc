#!/usr/bin/env bash

set -eux

rm -rf out/**/* || exit 0

python3 update.py out

cd out

if [ -z "$(git diff --exit-code)" ]; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

find .

export GIT_AUTHOR_NAME="github-actions[bot]"
export GIT_AUTHOR_EMAIL="41898282+github-actions[bot]@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

git add --all .
git commit -m "add: new IANA release $(cat .version)"
git push origin HEAD:iana-numbers

tag="$(cat .version)"
gh release delete "$tag" </dev/null || true
gh release create \
    --target iana-numbers \
    --title "$tag" \
    "$tag" \
    dist/iana-etc-* \
    </dev/null
