arr=(
    "bootstrap.min.css"
    "jquery-ui.min.css"
    "bootstrap.min.js"
    "jquery-ui.min.js"
    "jquery.min.js"
)
copyto=(
    "static/css/lib/bootstrap/bootstrap.min.css"
    "static/css/lib/jquery-ui/jquery-ui.min.css"
    "static/js/lib/bootstrap/bootstrap.min.js"
    "static/js/lib/jquery-ui/jquery-ui.min.js"
    "static/js/lib/jquery/jquery.min.js"
)

echo "" > runthis.sh


for f in "${!arr[@]}"; do 
    echo find ./node_modules/ -wholename "*dist*${arr[$f]}"
    initial=$(find ./node_modules/ -wholename "*dist*${arr[$f]}")
    echo "${arr[$f]} || ${copyto[$f]} || $initial"

    echo cp "$initial ${copyto[$f]}" >> runthis.sh
done 