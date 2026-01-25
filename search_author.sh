#!/usr/bin/env bash

gituser=$1

#set -x

if [[ $gituser == "" ]]; then
    cat <<EOF
usage: $o <github-user>

shows number of commits of gituser, sorts the branch names by commit count, shows date of last commiit.
EOF
    exit 1
fi

out=""
for branch in $(git branch -r); do
    if [[ $branch != "origin/HEAD" ]]; then
        cnt=$(git log ${branch} | grep -e '^Author:' | grep ${gituser} | wc -l | tr -d '[:space:]')
        if [[ $cnt != "0" ]]; then
            last_commit_date=$(git log ${branch} | grep -A 1 -e '^Author: '${gituser} | sed -n '2p')
            printf -v out "%s\n" "branch ${branch} user: ${gituser} commit-count: ${cnt} last_commit_date: ${last_commit_date}"
        fi
    fi
done

echo "${out}" 
#| sort -k 6,6n
