---
---

```
title: PRODUCTION deployment notes
host: http://tracks.stowers.org
uname: Linux tracks.stowers.org 2.6.32-431.29.2.el6.x86_64  +1 SMP Tue Sep 9 21:36:05 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
webserver: nginx runs as user nginx,
application runs under wsgi as user 'deployer'.
 + linux    user: deployer; password: c.f. /home/bioinfo/.passwords
 + postgres user: deployer; password: c.f. /home/bioinfo/.passwords
Required system packages: installed by root/system-administrator:
     +  python
     +  postgresql
     +  nginx
     +  uwsgi (recent source http://uwsgi-docs.readthedocs.org/en/latest/)
```

# Install

```{.bash}
yum install python # if needed
sudo yum -y install nginx
```

deployed using: nginx version: nginx/1.7.10	#
```
/usr/sbin/nginx -v
```

## Python database
is used for storage.
```{.bash}
sudo yum -y install postgresql postgresql-devel 
```

## sqlite

is used during development (i.e. when envirtonment variable
PRODUCTION is unset).  Install it also on production server to
enable testing/debugging.

```
sudo yum -y install sqlite-devel
```

## uwsgi

NB: it is NOT installed inside the venv but rather with the system
python.  ALL OTHER python packages are installed inside the venv.

```{.bash}
pip install uwsgi
```

# Configure

TODO?: put the configuration files under source control.

## nginx - the webserver

+ Create nginx.conf as service configuration file.  TODO: based on?

+ Create directory to hold 'sites' (one for each app, such as tracks):

```{.bash}
mkdir -p /etc/nginx/{sites-enabled,sites-available}
chown deployer sites-enabled sites-available
```

+ Create  /etc/nginx/sites-available/tracks
    +  TODO: based on?
    +  create symlinks from sites-available/tracks to sites-enabled/tracks

+ Create logging locations, to aggree with locations appearing in /etc/init.d/nginx

```{.bash}
mkdir -p /etc/nginx/logs/nginx/tracks/log
mkdir -p /etc/nginx/logs/nginx/log
mkdir -p /etc/nginx/logs/domains/tracks/log/
```



+ Disallow content indexing of tracks content by spiders (google, et al) using robots.txt
 + create /microarray/robots/robots.txt which contains the following:

```{.bash}
User-agent: *
Disallow: /
```

## uwsgi - the webserver/application interface protocol

 + /etc/init.d/uwsgi (TODO: as installed by ??? - apparently not by
 yum install uwsgi)

Key modifications:

```{.bash}
asdf
```

```{.bash}
OWNER=deployer
NAME=uwsgi
DESC=uwsgi
TRACKS_WSGI=/microarray/tracks/tracks/wsgi.py
VENV=/home/deployer/venv/

DAEMON_OPTS="--socket 127.0.0.1:8001 --wsgi-file ${TRACKS_WSGI} -M -t 30 -p 16 -b 32768 -d /var/log/$NAME.log --pidfile /var/run/$NAME/$NAME.pid --uid $OWNER --home=${VENV} --stats 127.0.0.1:9191"
DAEMON_OPTS+=" --env PRODUCTION=1"  # this had been missing.
```

## python libraries

Install and use virtual env in home directory of user deployer

```{.bash}
pip install --user virtualenv
cd $HOME
virtualenv venv

## activate the virtual python environment:
source ./venv/bin/activate
## install required packages INTO THE VIRTUAL ENVIRONMENT:
```{.bash}
pip install -r requirements.txt
pip install psycopg2
pip install pysqlite		# needed when PRODUCTION is unset (developing and debugging)
```

## Enviroment variables

NB: these are ONLY seen when django is run via `python manage.py
runserver`, but are NOT visible to the services, which is instead
controlled via ${DAEMON_OPTS} and ${TRACKS_WSGI}

```{.bash}
PRODUCTION=1		 	# NB: anything not empty is understood as 'production'
 # export PYTHONPATH=/microarray/tracks:$PYTHONPATH  # proved to be redundant with wsgi.py.
```

## postgres - the database 

```{.bash}
sudo -u postgres -s
/usr/local/pgsql/bin/createdb tracks
/usr/local/pgsql/bin/createuser -P deployer
GRANT ALL PRIVILEGES ON DATABASE tracks TO deployer;
\q
```

+ TODO: ddl for setting deployer database password!

## the database schema

Bring it up-to-date with the django model - in case of initial deployment, `syncdb` creates the tables for the
first time.

NOTE: manage.py is basic django command-line administration tool -
documented: https://docs.djangoproject.com/en/1.8/ref/django-admin/

```{.bash}
python manage.py syncdb
```

## the database content

Import previous tracks data into django (as had been exported (using
dumpdata) from previous version of tracks database)

 + previous tracks meta data had to be stream editted first (required
   changing the name of django model)


```{.bash}
sed -i tracks_redirect.json s/redirect.redirecthit/roasted.redirecthit/g tracks.json
cat tracks_redirect.json | sed 's/redirect.redirecthit/roasted.redirecthit/g' | sed 's/redirect.target/roasted.target/g' > new_tracks.json

python manage.py loaddata ../new_tracks.json 
```

# Run

## (re)start services:

NB: it is ESSENTIAL to test/confirm deployment using the /sbin/service
interface; even though it is _possible_ to directly execute
/etc/init.d/{uwsgi,nginx}, doing so causes it to run in whatever
happens to be the current environment, none of which is available when
run via /sbin/service (since /sbin/service executes the service in an
empty environment by using `env -i`).

```{.bash}
sudo /sbin/service nginx start # or restart
#sudo /sbin/service nginx reload
# ps -eaf | grep nginx		# observe /etc/nginx/nginx.conf is config file and worker process running as user nginx

sudo /sbin/service uwsgi start # or restart
```


# HOWTO
## use the environment variable PRODUCTION

PRODUCTION, when set, causes track.settings.production to be taken; it
need not be set to any particular value (such as 1).  Any value will
do.  Even the empty string.  You MUST 'unset PRODUCTION' to run
track.settings.dev.

## Test application logic using development server

`python manage.py runserver` allows you to launch django application
using its built-in server (i.e. not under nginx/uwsgi).  This Allows
testing application isolated from web depolyment considerations (of
nginx and uwsgi services, permissions, logs, process ownership, etc).

This will run in using tracks.settings.production, which forces uses
postgres (live) database:

    PRODUCTION=1 python manage.py runserver 


You can instead run using tracks.settings.dev (i.e. using
(development) sqlite3) database (and also with DEBUG=TRUE)

    PRODUCTION= python manage.py runserver

Setting `DEBUG=True` (as done by track.settings.dev), causes web pages
to render without css.  Not pretty. Addtionally providing --insecure
option "allow(s) serving static files even with DEBUG=True" (as set in
settings.dev):

    PRODUCTION= python manage.py runserver --insecure 

## stop and restart relevant services

```{.bash}
sudo /sbin/service uwsgi stop && sudo /sbin/service nginx stop && sudo /sbin/service uwsgi start && sudo /sbin/service nginx start
```

## create/update deployed schema to agree with django application model.

    PRODUCTION=1 python manage.py syncdb 

## move a copy of production data into development sqlite

    PRODUCTION=1 python manage.py dumpdata --indent 1 > dumpdata_PRODUCTION.json
    PRODUCTION=  python manage.py loaddata dumpdata_PRODUCTION.json

## watch various logs
```{.bash}
TRKLOGS=
TRKLOGS+=' /var/run/uwsgi/uwsgi.pid /var/run/nginx/nginx.pid '
TRKLOGS+=' /var/log/nginx/*.log /var/log/uwsgi.log'
TRKLOGS+=' /etc/nginx/logs/domains/tracks/log/*.log' # from  /etc/nginx/sites-enabled/tracks:
tail -f ${TRKLOGS}
```

## making source changes and deploy them

 + Check the code out onto your development host
 + do not do development on tracks server
 + get the source code using yourGithubAccount (which must be a member
   of the stowers metalhelix github organization).

```{.bash}
ssh you@yourDevHost
git clone 'https://<yourGithubAccount>@github.com/metalhelix/tracks.git'
 # ... make and test source code changes...
PRODUCTION= python manage.py runserver
git push orgin master # the simplist of workflows
ssh deployer@tracks.stowers.org # deploy your changes to production
cd /microarray
 # stop services
sudo /sbin/service nginx stop
sudo /sbin/service uwsgi stop
 # update source from git
git pull
 # restart services
sudo /sbin/service nginx start
sudo /sbin/service uwsgi start
```

## produce htmlized version of this document

```{.bash}
pandoc  -s -S --toc -c http://pandoc.org/demo/pandoc.css --read=markdown -o production_install_notes.html  production_install_notes.md
```

# ISSUE

The following ISSUES were identified and resolved by Malcolm and Jenny
while sleuthing the fix for the fact that the url dispatch was not
working correctly on the deployed tracks server.

## PRODUCTION was not being communicated to track.settings.

There are at least two ways to do this, neither of which was
happening.  I chose to communicate it as an option to the call to wsgi
made in the service script via /etc/init.d/uwsgi which has it
hardcoded to 1:

       DAEMON_OPTS+=" --env PRODUCTION=1"

Alternatively, it could be set in the file tracks/wsgi.py.  Putting
this option in the init.d file causes the service to always run in
PRODUCTION, which is desired on this server.  It also allows for
testing/non-production when application launched by `python manage.py`

Similarly, DJANGO_SETTINGS_MODULE could be set in either the init.d
service script, as:

	 DAEMON_OPTS+=" --env DJANGO_SETTINGS_MODULE=tracks.settings"

of in wsgi.py.  This latter is more appropriate - the setting is
intrinsic to the application and need never be changed depending on
production or testing/developing.


## the relocation of /var/run/uwsgi.pid to /var/run/uwsgi/uwsgi.pid was incomplete.

An additional corresponding change was needed: the daemon invocation
needs to include the --pifile option BEFORE the $prog:

    daemon --pidfile /var/run/$NAME/$NAME.pid $prog $DAEMON_OPTS

or get errors logged in process take-down, such as:

    2015/04/28 14:26:08 [alert] 2918#0: unlink() "/var/run/nginx.pid" failed (2: No such file or directory)

## track.settings.production were hard-coded into manage.py

This made it not possible to test deployment in development
(i.e. using sqlite). It now loads track.settings, which in turn
dispatches on PRODUCTION being set.  Not required to fix the issue,
but identified during debugging.

## log rotation was not configured to respect modified file

ownership (i.e. the /var/log/uwsgi.log is ownded by `deployer`).

RESOLUTION: modify log rotation to create new log as user deployer.

FIXME: also, change cat /etc/logrotate.d/nginx

## file:requirements.txt had not been (fully?) sourced into the activated python virtual environment.

Jenny had started to identify missing modules and add them to the
system python - this was inconsistent with deployment plan''s use of

Resolution: rerun the `pip install` in a shell after having first
sourced /microarray/tracks/venv/bin/activate.

## uwsgi service owner management

Control of wsgi worker processes was weak.  The service is started by
root (on system boot).  As deployed, it appeared to have been
depending upon the service having been started by user deployer.

Resolution: Jenny's addition of "--uid ${OWNER}" to the call to uswgi
in /etc/init.d/uswgi.

## bad web config rewrites

The /etc/nginx/sites-available/tracks configuration file had rewrites
which were interfering with url dispath in tracks.urls.py.

Resolution: reverse the commenting on these two lines so that trailing
slashes are NOT removed.  This was the crux of the issue.

TODO: what was the history of changes to this file; was it changed for
some other reason?

    rewrite ^([^.]*[^/])$ $1/ permanent; # If the URI doesn't have a period and does not end with a slash, add a slash to the end
    # rewrite ^/(.+)/$ /$1 permanent; # remove trailing slash

