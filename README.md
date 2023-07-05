## gittools - understand your organization, by looking at the git log of your project

The script [git-whoiswho.py](https://raw.githubusercontent.com/MoserMichael/gittools/main/git-whoiswho.py) is reading and analysing the git log for the git repository in the current directory.

For each author it is displaying the number of commits, number of files touched by all of the commit (the sum of files in each of the commits), number of lines added/changed/deleted (approximation). How long each author has been active (that's the date of the last commit minus the date of the first commit), what is the mean duration of this 'tenure' for each author, what is the standard deviation of this metric, etc.

I think this might get some indication of who is who - when joining a new project / new organisation. 

Hope that this tool might be of help.

