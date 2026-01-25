#!/usr/bin/env bash

gituser=$1

#set -x

if [[ $gituser == "" ]]; then
    cat <<EOF
usage: $o <github-user>

shows number of commits of gituser in all remote branches, sorts the branch names by commit count, shows date of last commiit.

Note: does not search the local branch
Note: don't forget to run git fetch - before running this script (git fetch synchs the remote branches)
EOF
    exit 1
fi

out=""
for branch in $(git branch -r | awk '{print $1}'); do
    if [[ $branch != "origin/HEAD" ]]; then
        cnt=$(git log ${branch} | grep -e '^Author: '${gituser} | wc -l | tr -d '[:space:]')
        if [[ $cnt != "0" ]]; then
            last_commit_date=$(git log ${branch} | grep -A 1 -e '^Author: '${gituser} | sed -n '2p')
            printf -v out "%s\n%s" "${out}" "branch ${branch} user: ${gituser} commit-count: ${cnt} last_commit_date: ${last_commit_date}"
        fi
    fi
done

echo "${out}" | sort -k 6,6n
