# Important Note About Git Hooks

On most git actions, the `.git/hooks` directory is overwritten with the content of 
`/git-misc/git-hooks`, from the repository. This keeps hooks synced among all clients.

Don't make changes to .git/hooks directly, they'll just be lost. Make changes to `/git-misc/git-hooks`,
and commit them to the repo.

If you need user-specific hooks, make a directory called `/git-misc/git-hooks-nosync` and place them there.
Any files found within that directory will be copied to `.git/hooks` AFTER the main git-hooks directory. 
Note, if files in the nosync directory are the same name as files in the general hooks directory, they will
overwrite them. Use with caution.
