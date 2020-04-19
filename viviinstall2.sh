sudo apt install apache2 build-essential certbot debhelper emacs enchant fail2ban fonts-ubuntu-console git htop ldap-utils libapache2-mod-wsgi-py3 libjpeg-dev ntp python3-all-dbg python3-all-dev python3-doc python3-pip python3-venv python-all-dbg python-all-dev python-certbot-apache python-doc python-egenix-mx-base-dev python-ldap python-sphinx quilt sasl2-bin sendmail systemd-sysv tcsh units zsh zsh-doc npm postgresql postgresql-server-dev-10 libjpeg-dev -y
sudo apt install python3.7-dev python3.7-venv sqlite3 -y

git clone git@github.com:violetbp/chez-betty.git

cd chez-betty

#install node
curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -
sudo apt-get install -y nodejs



python3.7 -m venv env
source env/bin/activate

pip install wheel
pip install -e .
python setup.py develop

pip uninstall -y zope.interface zope.sqlalchemy
pip install zope.deprecation==4.4.0 zope.interface==4.6.0 zope.sqlalchemy==1.1


mkdir chezbetty/static/js/lib

# sudo npm install bower bower-installer -g
# bower-installer
#using yarn now
#yarn
sudo npm i yarn -g
yarn

# Database stuff 
sqlite3 chezbetty.sqlite3 ""
path="sqlalchemy.url = sqlite:///`pwd`/chezbetty.sqlite3"
path=${path//\//\\\/} #replace the backslashes with escaped ones
sed "s/sqlalchemy.url = sqlite:\/\/\/%(here)s\/chezbetty.sqlite/$path/" development.ini.example >development.ini
#run initialziation script
python chezbetty/initializedb.py development.ini



echo "source env/bin/activate"
echo "pserve development.ini"