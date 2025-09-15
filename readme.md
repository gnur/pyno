# pyno

pyno is the minimal companion for your notes:

- api to add notes
- automatically creates a daily note (and cleans it up if nothing was added)
- automatically keeps your todo list up to date on your daily note

## this repo

### main.py
uv compatible python script with inlinde dependencies

### en
`./en` is the old implementation in bash, with limited functionality


## todo

- [x] add function that creates "daily" note
      copy all unfinished todo items from the last previous note
      add date of last daily note to todo items without date
- [ ] add api endpoint that can accept notes
      add content of request to today note
- [ ] add watcher that will automatically create the daily note after midnight
      if the last daily note only has a todo list that is the same as the daily note before it should be automatically be deleted because it has no new content
