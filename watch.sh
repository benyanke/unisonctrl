file="/home/benyanke/git/unisonctrl/unisonctrl/unisonhandler.py"
watch="/home/benyanke/git/unisonctrl/unisonctrl/*.py"

function run() {
  clear;
  $file
}

run;

inotifywait -q -m -e close_write --format %e $watch |
while read events; do
  run;
done


