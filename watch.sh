file="/home/benyanke/git/unisonctl/unisonctl/unisonhandler.py"
watch="/home/benyanke/git/unisonctl/unisonctl/*.py"

function run() {
  clear;
  $file
}

run;

inotifywait -q -m -e close_write --format %e $watch |
while read events; do
  run;
done


