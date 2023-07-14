#!/usr/bin/env python

import subprocess
import shlex
import functools
from datetime import datetime
import operator
import statistics
import sys
import os

class Options:
    def __init__(self):
        self.show_progress = True
        self.sort_by_field = 'num_commits'
        self.sort_descending  = True
        self.author_join_leave_resolution = 24 * 3600 * 30.5 * 4  # four 'months' default
        self.show_joining_leaving = True


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

class CommitEntry:

    FILE_STATUS_DELETED=1
    FILE_STATUS_ADDED=2
    FILE_STATUS_CHANGED=3

    def __init__(self, hash_val, author, email, time):
        self.hash_val = hash_val
        self.author = author
        self.email = email
        self.time = time

        # data added upon analysing the commit
        self.files_added = 0
        self.files_deleted = 0
        self.files_changed = 0

        self.lines_added = 0
        self.lines_deleted = 0
        self.lines_changed = 0


    def show(self):
        print(f"File: A/D/C {self.files_added}/{self.files_deleted}/{self.files_changed}  Lines: A/D/C {self.lines_added}/{self.lines_deleted}/{self.lines_changed}")

    def _get_commit_text(self):
        #cmd = f"git show --no-color {self.hash_val}"
        cmd = f"git show --no-color --pretty='format:%b' {self.hash_val}"
        cmd_out=RunCommand(cmd)

        return cmd_out.output


    def analyse(self):
        line_status = 0
        deleted_line_seq = 0
        added_line_seq = 0

        for line in self._get_commit_text().split("\n"):
            if line.startswith("---"):
                if line.find("/dev/null") == -1:
                    line_status += CommitEntry.FILE_STATUS_DELETED
            elif line.startswith("+++"):
                if line.find("/dev/null") == -1:
                    line_status += CommitEntry.FILE_STATUS_ADDED
            else:
                if line_status != 0:
                    if line_status == CommitEntry.FILE_STATUS_DELETED:
                        self.files_deleted += 1
                    elif line_status == CommitEntry.FILE_STATUS_CHANGED:
                        self.files_changed += 1
                    elif line_status == CommitEntry.FILE_STATUS_ADDED:
                        self.files_added += 1

                    line_status = 0

                    if added_line_seq > 0 or deleted_line_seq > 0:
                        self.on_line_sequence(added_line_seq, deleted_line_seq)

                    added_line_seq = 0
                    deleted_line_seq = 0


                if line.startswith("-"):
                    deleted_line_seq += 1
                elif line.startswith("+"):
                    added_line_seq += 1
                else:
                    if added_line_seq !=0 or deleted_line_seq != 0:
                        self.on_line_sequence(added_line_seq, deleted_line_seq)
                        added_line_seq = 0
                        deleted_line_seq = 0

        if added_line_seq != 0 or deleted_line_seq != 0:
            self.on_line_sequence(added_line_seq, deleted_line_seq)


    def on_line_sequence(self, added_line_seq, deleted_line_seq):
        self.lines_changed += min(added_line_seq, deleted_line_seq)
        if  added_line_seq > deleted_line_seq:
            self.lines_added += added_line_seq - deleted_line_seq
        else:
            self.lines_deleted += deleted_line_seq - added_line_seq


class Author:
    def __init__(self, author, email):
        self.author = author
        self.email = email
        self.commits = []

    def add_commit(self, commit):
        self.commits.append(commit)

    def display_name(self):
        auth = self.author.strip()
        if auth == "":
            auth = self.email
        return auth

    def analyse(self):
        self.files_added = functools.reduce(lambda x, commit : x + commit.files_added, self.commits, 0)
        self.files_deleted = functools.reduce(lambda x, commit : x + commit.files_deleted, self.commits, 0)
        self.files_changed = functools.reduce(lambda x, commit : x + commit.files_changed, self.commits, 0)
        self.files_affected = self.files_added + self.files_deleted + self.files_changed

        self.lines_added = functools.reduce(lambda x, commit : x + commit.lines_added, self.commits, 0)
        self.lines_deleted = functools.reduce(lambda x, commit : x + commit.lines_deleted, self.commits, 0)
        self.lines_changed = functools.reduce(lambda x, commit : x + commit.lines_changed, self.commits, 0)
        self.lines_affected =  self.lines_added + self.lines_deleted + self.lines_changed

        self.from_date = min(self.commits, key=lambda x: x.time).time
        self.to_date = max(self.commits, key=lambda x: x.time).time
        self.tenure = self.to_date - self.from_date
        self.num_commits = len(self.commits)

    def show(self):
        ftime = datetime.utcfromtimestamp(self.from_date).strftime('%Y-%m-%d')
        ttime = datetime.utcfromtimestamp(self.to_date).strftime('%Y-%m-%d')

        print(f"Author: {self.author}, mail: {self.email}, Num-of-commits: {self.num_commits}, files:(Added/Deleted/Changed): {self.files_added}/{self.files_deleted}/{self.files_changed}, lines(Added/Deleted/Changed):{self.lines_added}/{self.lines_deleted}/{self.lines_changed}, time-range: {ftime} to {ttime}")


class AuthorEvent:

    def __init__(self):
        self.author_first_commit = []
        self.author_last_commit = []

    def add_author_first_commit(self, author):
        self.author_first_commit.append(author)

    def add_author_last_commit(self, author):
        self.author_last_commit.append(author)


class GitRepoData:

    def __init__(self, opts):
        self.authors = {}
        self.first_commit = sys.maxsize
        self.last_commit  = -sys.maxsize
        self.join_leave = None
        self.opts = opts

    def analyse(self):
        self._get_commits()
        self._analyse()
        self._sort_for_display()
        self._analyse_join_and_leave_authors()

    def _analyse_join_and_leave_authors(self):
        num_units = int((self.last_commit - self.first_commit) / self.opts.author_join_leave_resolution) + 1
        self.join_leave = [ None ] * num_units

        for author in self.authors.values():
            join_idx = int( (author.from_date - self.first_commit) / self.opts.author_join_leave_resolution )
            if not self.join_leave[join_idx]:
                self.join_leave[join_idx] = AuthorEvent()
            self.join_leave[join_idx].add_author_first_commit(author)

            leave_idx = int( (author.to_date - self.first_commit) / self.opts.author_join_leave_resolution )
            if not self.join_leave[leave_idx]:
                self.join_leave[leave_idx] = AuthorEvent()
            self.join_leave[leave_idx].add_author_last_commit(author)


    def _analyse(self):
        for author in self.authors.values():
            author.analyse()

    def show(self):
        print("")
        for commit in self.display_list:
            commit.show()

        self._show_tenure()

        print("\nDYNAMICS IN CHANGE OF COMMITTERS\n")

        self._show_join_leave()

        print("")

    def _show_tenure(self):
        print("\nAuthor statistics (tenure is defined as time between first and last commit)\n\n")
        print(f"Number of authors: {len(self.display_list)}")
        tenures = []
        for auth in self.display_list:
            tenures.append(auth.tenure)

        max_tenure = max(tenures)
        mean_tenure = statistics.mean(tenures)
        stddev_tenure = statistics.pstdev(tenures)

        print(f"Mean tenure:    {GitRepoData._to_months(mean_tenure)} months")
        print(f"Stddev tenure:  {GitRepoData._to_months(stddev_tenure)} months")
        print(f"Maximum tenure: {GitRepoData._to_months(max_tenure)} months")

    def _show_join_leave(self):
        from_time = cur_time = self.first_commit
        current_headcount = 0

        current_authors=set()


        for index, event in enumerate(self.join_leave):
            cur_time += self.opts.author_join_leave_resolution
            if cur_time > self.last_commit:
                cur_time = self.last_commit

            is_last = index == len(self.join_leave) - 1

            if event:
                current_headcount = self._show_one(current_headcount, from_time, cur_time, event, current_authors, is_last)
                from_time = cur_time

    def _show_one(self, current_headcount, from_time, to_time, event, current_authors, is_last):

        joined = len(event.author_first_commit)
        left = 0
        if not is_last:
            left = len(event.author_last_commit)
        next_headcount = current_headcount  + joined - left

        sfrom =  datetime.utcfromtimestamp(from_time).strftime('%H:%M %Y-%m-%d')
        sto   =  datetime.utcfromtimestamp(to_time).strftime('%H:%M %Y-%m-%d')

        for auth in event.author_first_commit:
            current_authors.add(auth)
        if not is_last:
            for auth in event.author_last_commit:
                current_authors.remove(auth)


        print(f"{sfrom} - {sto}: headcount at start: {current_headcount}, joined: {joined} left: {left} headcount at end: {next_headcount}")

        if self.opts.show_joining_leaving:
           if len(event.author_first_commit): 
               print("\tfirst-commit:\t", end="")
               for auth in event.author_first_commit:
                   print( auth.display_name(), end=", ")
           if not is_last and len(event.author_last_commit):
               print("\n\tlast-commit:\t", end="")
               for auth in event.author_last_commit:
                   print( auth.display_name(), end=", ")
           print("")

        if is_last:
            print("\n\nCurrently active authors:\n")
            for auth in current_authors:
                print( auth.display_name(), end=", ")

        return  next_headcount

    def _to_months(val):
        return val / (24 * 3600 * 30.5)

    def _sort_for_display(self):
        self.display_list = list(self.authors.values())
        self.display_list.sort(key=operator.attrgetter(self.opts.sort_by_field), reverse=self.opts.sort_descending)

    def _get_commits(self):
        cmd=RunCommand("git log --format='%H,%aN,%ae,%ct'")
        commit_num = 0
        for line in cmd.output.split("\n"):
            line = line.strip()
            if line != "":
                if self.opts.show_progress:
                    commit_num += 1
                    if commit_num % 10 == 0:
                        print(".", end='', flush=True)
                #print(f"line: {line}")
                [ hash_val, author, author_mail, commit_date_s]  = line.split(',')

                commit_date = int(commit_date_s)

                self.first_commit = min(self.first_commit, commit_date)
                self.last_commit = max(self.last_commit, commit_date)

                #print(f"{hash_val} - {author} - {commit_date}")
                commit = CommitEntry(hash_val, author, author_mail, commit_date)

                author_obj = self.authors.get(author)
                if not author_obj:
                    author_obj = Author(author, author_mail)
                    self.authors[author] = author_obj

                commit.analyse()
                author_obj.add_commit(commit)

def main():

    if len(sys.argv) == 2 and (sys.argv[1] == '-h' or os.environ.get("SHORT_HELP_MODE")):
        print("Shows how many commits/files/lines any one of the users made, shows how long each of the users have been active.")
        sys.exit(1)

    opt = Options()
    run = GitRepoData(opt)
    run.analyse()
    run.show()



if __name__ == '__main__':
    main()
