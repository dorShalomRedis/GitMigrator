# GitMigrator
Simple python script for migrating files between git repositories using git-filter-repo.
It was created for specific task [SM to SM-UI-Refresh Migration](https://github.com/redislabsdev/SM-UI-Refresh/blob/develop/automation/readme/file-migration.md), but should work for any other migration between 2 existing repos.

In high level the script takes a file or directory from a source repo and deletes all the repo's history except the requested files and their history.
Then it adds them to the requested path in the dest repo.
The rest of the work should be done manually.

## Install 
`python3 setup.py install`

## Use
1. edit the `params.json` file
2. run `python3 main.py`
