---
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
---


```sh
yum install python # if needed
sudo yum -y install nginx
```

deployed using: nginx version: nginx/1.7.10	#
```
/usr/sbin/nginx -v
```


## Python database
is used for storage.
```sh
sudo yum -y install postgresql postgresql-devel 
```

## sqlite

is used during development (i.e. when envirtonment variable
PRODUCTION is unset).  Install it also on production server to
enable testing/debugging.

```
sudo yum -y install sqlite-devel
```

pip install uwsgi 
### NB: uwsgi is NOT installed inside the venv but rather with the
### system python.  ALL OTHER python packages are installed inside the
### venv.

mkdir -p /etc/nginx/{sites-enabled,sites-available}
chown deployer sites-enabled sites-available

# create nginx.conf - TODO: based on?
# create /etc/nginx/sites-available/tracks - TODO: based on?
# TODO?: put these under source control.
# create symlinks from sites-available/tracks to sites-enabled/tracks

### configure logging locations (as declared in /etc/init.d/nginx)
mkdir -p /etc/nginx/logs/nginx/tracks/log
mkdir -p /etc/nginx/logs/nginx/log
mkdir -p /etc/nginx/logs/domains/tracks/log/

### set up database
sudo -u postgres -s
/usr/local/pgsql/bin/createdb tracks
/usr/local/pgsql/bin/createuser -P deployer
GRANT ALL PRIVILEGES ON DATABASE tracks TO deployer;
\q

### TODO: ddl for setting deployer database password!

### TODO: put this file under source control.  modify
### /etc/init.d/uwsgi (TODO: as installed by ??? - apparently not by
### `yum install uwsgi`) with appropriate daemon configs:
OWNER=deployer
NAME=uwsgi
DESC=uwsgi
TRACKS_WSGI=/microarray/tracks/tracks/wsgi.py
VENV=/home/deployer/venv/

DAEMON_OPTS="--socket 127.0.0.1:8001 --wsgi-file ${TRACKS_WSGI} -M -t 30 -p 16 -b 32768 -d /var/log/$NAME.log --pidfile /var/run/$NAME/$NAME.pid --uid $OWNER --home=${VENV} --stats 127.0.0.1:9191"
DAEMON_OPTS+=" --env PRODUCTION=1"  # this had been missing.

## install virtual env in deployer home
pip install --user virtualenv
cd $HOME
virtualenv venv
## activate the virtual python environment:
source ./venv/bin/activate
## install required packages INTO THE VIRTUAL ENVIRONMENT:
pip install -r requirements.txt
pip install psycopg2
pip install pysqlite		# needed when PRODUCTION is unset (developing and debugging)

## Set enviromental variables. NB: these are ONLY seen when django is run
## via `python manage.py runserver`, but are NOT visible to the
## services, which is instead controlled via ${DAEMON_OPTS} and ${TRACKS_WSGI}
PRODUCTION=1		 	# NB: anything not empty is understood as 'production'
# set python path
# THIS WAS NOT NEEDED: export PYTHONPATH=/microarray/tracks:$PYTHONPATH

## bring the database schema up-to-date with the django model - in
## case of initial deployment, `syncdb` creates the tables for the
## first time.
python manage.py syncdb
## NOTE: manage.py is basic django command-line administration tool -
## documented:
## https://docs.djangoproject.com/en/1.8/ref/django-admin/

## migrate previous tracks meta data (required changing the name of
## django model)
sed -i tracks_redirect.json s/redirect.redirecthit/roasted.redirecthit/g tracks.json
cat tracks_redirect.json | sed 's/redirect.redirecthit/roasted.redirecthit/g' | sed 's/redirect.target/roasted.target/g' > new_tracks.json

## Import previous tracks data into django (as had been exported (using dumpdata)
## from previous version of
## tracks database)
python manage.py loaddata ../new_tracks.json 

## Disallow content indexing of tracks content by spiders (google, et al) using robots.txt.  .  configure nginx's with a robots.txt 
## /microarray/robots/robots.txt which contains the following:
User-agent: *
Disallow: /

## (re)start services:
sudo /sbin/service nginx start # or restart
#sudo /sbin/service nginx reload
# ps -eaf | grep nginx		# observe /etc/nginx/nginx.conf is config file and worker process running as user nginx

sudo /sbin/service uwsgi start # or restart
## NB: it is ESSENTIAL to test/confirm deployment using the
## /sbin/service interface; even though it is _possible_ to directly
## execute /etc/init.d/{uwsgi,nginx}, doing so causes it to run in
## whatever happens to be the current environment, none of which is
## available when run via /sbin/service (since /sbin/service executes
## the service in an empty environment by using `env -i`).

## DEBUGGING NOTES, LESSONS, CODE CHANGES, TASKS LEARNED

The following notes were taken while sleuthing the fix for the fact
that the url dispatch was not working on the deployed tracks server.


* HOWTO: stop and restart relevant services

```
sudo /sbin/service uwsgi stop && sudo /sbin/service nginx stop && sudo /sbin/service uwsgi start && sudo /sbin/service nginx start
```

* WHATIS: the environment variable PRODUCTION?

must simply exist for track.settings.production to be used; it need
not be set to any particular value (such as 1).  Any value will do.
Even the empty string.  You MUST 'unset PRODUCTION' to run
track.settings.dev.

* ISSUE: PRODUCTION was not being communicated to track.settings.

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


ISSUE: the relocattion of /var/run/uwsgi.pid to
/var/run/uwsgi/uwsgi.pid was incomplete.

An additional corresponding change was needed: the daemon invocation
needs to include the --pifile option BEFORE the $prog:

  daemon --pidfile /var/run/$NAME/$NAME.pid $prog $DAEMON_OPTS

 or get errors logged in process take-down, such as:

 2015/04/28 14:26:08 [alert] 2918#0: unlink() "/var/run/nginx.pid" failed (2: No such file or directory)

* manage.py had hard-coded track.settings.production.  no longer!
Rather, it now loads track.settings, which in turn dispatches on
PRODUCTION being set.  Not required to fix the issue, but identified
during debugging.

* ISSUE: log rotation was not configured to respect modified file
ownership (i.e. the /var/log/uwsgi.log is ownded by `deployer`).

RESOLUTION: modify log rotation to create new log as user deployer.

FIXME: also, change cat /etc/logrotate.d/nginx

* ISSUE: file:requirements.txt had not been (fully?) sourced into the
activated virtual environment.

Jenny had started to identify missing modules and add them to the
system python - this was inconsistent with deployment plan''s use of

Resolution: rerun the `pip install` in a shell after having first
sourced /microarray/tracks/venv/bin/activate.

* ISSUE: The addition (made by jenny?) of "--uid ${OWNER}" to the call
to uswgi in /etc/init.d/uswgi is needed since the service is started
by root (on system boot)

* ISSUE: The /etc/nginx/sites-available/tracks configuration file had
rewrites which were interfering with url dispath in tracks.urls.py.

Resolution: reverse the commenting on these two lines so that trailing
slashes are NOT removed.  This was the crux of the issue.

TODO: what was the history of changes to this file; was it changed for
some other reason?

  rewrite ^([^.]*[^/])$ $1/ permanent; # If the URI doesn't have a period and does not end with a slash, add a slash to the end
  # rewrite ^/(.+)/$ /$1 permanent; # remove trailing slash

TODO: source control this file?

## HOWTO: ADMINISTRATIVE TASKS

### run development server  (not under nginx/uwsgi) using
### tracks.settings.production (i.e. using postgres)
PRODUCTION=1 python manage.py runserver

### run development server (not under nginx/uwsgi) using
### tracks.settings.production (i.e. using postgres)
PRODUCTION= python manage.py runserver # run using tracks.settings.dev (i.e. using sqlite3)

### ditto, without which css are not loading - "allow serving static
### files even with DEBUG=True" (as set in settings.dev)
PRODUCTION= python manage.py runserver --insecure 

### create/update deployed schema to agree with django application
### model.
PRODUCTION=1 python manage.py syncdb 

### move a copy of production data into development mysql
PRODUCTION=1 python manage.py dumpdata --indent 1 > dumpdata_PRODUCTION.json
PRODUCTION=  python manage.py loaddata dumpdata_PRODUCTION.json



### HOWTO: making source changes and deploy them
# check it out onto your development host (do not do development on tracks server)
ssh you@yourDevHost
# get the source code using yourGithubAccount (which must be a member
# of the stowers metalhelix group).
git clone 'https://<yourGithubAccount>@github.com/metalhelix/tracks.git'
# make source code changes
# test them:
PRODUCTION= python manage.py runserver
# commit changes to repos
git
# deploy your changes to production
ssh deployer@tracks.stowers.org
cd /microarray
# stop services
sudo /sbin/service nginx stop
sudo /sbin/service uwsgi stop
# update source from git
git pull
# restart services
sudo /sbin/service nginx start
sudo /sbin/service uwsgi start


### watch various logs:
TRKLOGS=
TRKLOGS+=' /var/run/uwsgi/uwsgi.pid /var/run/nginx/nginx.pid '
TRKLOGS+=' /var/log/nginx/*.log /var/log/uwsgi.log'
# from  /etc/nginx/sites-enabled/tracks:
TRKLOGS+=' /etc/nginx/logs/domains/tracks/log/*.log'
tail -f ${TRKLOGS}

