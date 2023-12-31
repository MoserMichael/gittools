#!/usr/bin/python3

import sys
import shlex
import subprocess
import re

def show_error(msg):
    print("Error: {}".format(msg))
    sys.exit(1)


def count_changed_lines(hash_val):

    cmd="git show " + hash_val
    run_cmd = RunCommand(cmd)

    if run_cmd.exit_code == 0:
        lines_added = 0
        lines_removed = 0

        for line in run_cmd.output.splitlines():
            if line[:4] != "--- " and line[:4] != "+++ ":
                if line[:1] == "+":
                    lines_added += 1
                if line[:1] == "-":
                    lines_removed += 1

        return lines_added, lines_removed
    return 0, 0

class RunCommand:
    def __init__(self, command_line):
        self.command_line = command_line
        self.exit_code = 0
        self.run(command_line)

    def run(self, command_line):
        try:
            process = subprocess.Popen(shlex.split(command_line), \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            (output, error_out) = process.communicate()
            self.exit_code = process.wait()

            self.output = output.decode("cp858")
            self.error_out = error_out.decode("cp858")
            self.exit_code = process.wait()
            return self.exit_code

        except FileNotFoundError:
            self.output = ""
            self.error_out = "file not found"
            self.exit_code = 1
            return self.exit_code

    def status(self):
        return self.exit_code

class Main:
    def __init__(self):
        self.date_to_commitcount={}
        self.date_to_uniquefilescommited={}
        self.date_to_num_of_commits={}
        self.date_to_committercount={}

        self.run_cmd()

    def run_cmd(self):
        if len(sys.argv) == 2 and sys.argv[1] == '-h':
            print("show how many files were commited to git repo in current dir per month")
            sys.exit(1)

        cmd="git log --pretty='commit:: %ad %ae %H' --name-only --date=format:%Y-%m"

        run_cmd = RunCommand(cmd)

        if run_cmd.exit_code != 0:
            show_error("current directory is not a git repo")

        self.run_scan(run_cmd.output.splitlines())
        self.show_report()



    def run_scan(self,lines):

        for line in lines:
            match_obj = re.match(r'commit:: (.*) (.*) (.*)', line)
            if not match_obj and line !="":
                res = self.date_to_commitcount.get(date)
                if not res:
                    self.date_to_commitcount[date] = 1
                else:
                    self.date_to_commitcount[date] = self.date_to_commitcount[date] + 1

                res = self.date_to_uniquefilescommited.get(date)
                if not res:
                    self.date_to_uniquefilescommited[date] = { line : "1" }
                else:
                    self.date_to_uniquefilescommited[date][line] = "1"

                self.date_to_committercount[date][author_email][1] += 1
                continue
            if not match_obj and line == "":
                continue

            ###
            date = match_obj.group(1)
            author_email = match_obj.group(2)
            commit_hash = match_obj.group(3)

            lines_count = count_changed_lines(commit_hash)

            res = self.date_to_num_of_commits.get(date)
            if not res:
                self.date_to_num_of_commits[date] = 1
            else:
                self.date_to_num_of_commits[date] += 1

            res = self.date_to_committercount.get(date)
            if not res:
                self.date_to_committercount[date] = { author_email : \
                                    [1, 0, lines_count[0], lines_count[1] ] }
            else:
                res2 = res.get(author_email)
                if not res2:
                    res[author_email] = [1, 0, lines_count[0], lines_count[1] ]
                else:
                    res[author_email][0]+= 1
                    res[author_email][2]+= lines_count[0]
                    res[author_email][3]+= lines_count[1]

    def show_report(self):

        for k in sorted(self.date_to_commitcount.keys()):
            print("month: {} num-of-commits-per-month {}\tnumber-of-files-commited: {}\
                    \tunique-files-commited: {}".\
                    format(k,\
                        self.date_to_num_of_commits[k],\
                        self.date_to_commitcount[k], \
                        len(self.date_to_uniquefilescommited[k]) \
                        ))

            authors = list(self.date_to_committercount[k].keys())
            authors.sort(key=lambda x: self.date_to_committercount[k][x][0], reverse=True)

            for author in authors:
                print("\tnum-commits: {}\tfiles-changed-in-commits: {}\t\
lines added/removed {}/{}\t author: {}".\
                        format(self.date_to_committercount[k][author][0], \
                               self.date_to_committercount[k][author][1], \
                               self.date_to_committercount[k][author][2], \
                               self.date_to_committercount[k][author][3], \
                               author))

Main()
