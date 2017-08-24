file="/home/benyanke/git/unisonctrl/unisonctrl/unisonhandler.py"
watch="/home/benyanke/git/unisonctrl/unisonctrl/*.py"

function run() {
   clear;
   echo "Copying"
   scp unisonctrl/*.py pcnartsync:/opt/unisonctrl/unisonctrl/
#   clear;
#  $file
#  flake8
}

run;

inotifywait -q -m -e close_write --format %e $watch |
while read events; do
  run;
done


