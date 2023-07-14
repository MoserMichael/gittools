## gittools - understand your organization, by looking at the git log of your project

A collection of scripts for analysing the output of ```git log```. When running these scripts: the current directory needs to be within a git repository.

---

Script [git-whoiswho.py](https://raw.githubusercontent.com/MoserMichael/gittools/main/git-whoiswho.py) is reading and analysing the git log for the git repository in the current directory.

Reads the git log of the repository in the current directory. For each author it is displaying the number of commits that were submitted by the author, number of files touched by all of the commit (the sum of files in each of the commits), number of lines added/changed/deleted (approximation). How long each author has been active (that's the date of the last commit minus the date of the first commit), what is the mean duration of this time range for each author, what is the standard deviation of this metric. There is also a section on the dynamics of the commiters - how many joined/left during a quarter, who are the commiters currently active...

I think this might get some indication of 'who is who'. This information might be of use when joining a new project / new organisation.

---

Script [whenwasthischanged.py](https://raw.githubusercontent.com/MoserMichael/gittools/main/whenwasthischanged.py) - breakdown per months: how many commits were made per month by who?

---

Script [whochangedthisrepolast.sh](https://raw.githubusercontent.com/MoserMichael/gittools/main/whochangedthisrepolast.sh) - for each files in current git repo - show who made the last revision.
Show a summary of how many files were modified last per user

[whochangedthisrepofirst.sh](https://raw.githubusercontent.com/MoserMichael/gittools/main/whochangedthisrepofirst.sh) - shows who made the first commit for each file that is currently in the repo

---

Hope that these scripts might be of help.

