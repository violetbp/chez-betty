mkdir -p chezbetty/static/css/lib/bootstrap/ chezbetty/static/js/lib/bootstrap/ chezbetty/static/js/lib/jquery/
mkdir -p chezbetty/static/js/lib/jquery-ui/ chezbetty/static/css/lib/jquery-ui/

cp ./node_modules/bootstrap/dist/css/bootstrap.min.css chezbetty/static/css/lib/bootstrap/bootstrap.min.css
cp ./node_modules/bootstrap/dist/js/bootstrap.min.js chezbetty/static/js/lib/bootstrap/bootstrap.min.js
cp ./node_modules/jquery/dist/jquery.min.js chezbetty/static/js/lib/jquery/jquery.min.js


mkdir temp
pushd temp
wget https://jqueryui.com/resources/download/jquery-ui-1.12.1.zip
unzip jquery-ui-1.12.1.zip
pushd jquery-ui-1.12.1
cp  jquery-ui.min.css ../../chezbetty/static/css/lib/jquery-ui/jquery-ui.min.css
cp  jquery-ui.min.js ../../chezbetty/static/js/lib/jquery-ui/jquery-ui.min.js
popd
popd