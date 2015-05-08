# Overview

This document describes the Stowers 'tracks' server, which was
developed by <Sam.Meier@gmail.com> with requirements and encouragement
from <Chris_Seidel@stowers.org>.  It is currently administered jointly
between <Jenny_McGee@stowers.org> and <Malcolm_Cook@stowers.org>.  The
document started as Sam's leave-behind, and have been added to by
Malcolm as he reviewed the application's deployment and overcame some
of the ISSUES identified herein.

This project, and this file, is on github at
<https://github.com/metalhelix/tracks>.  It is private - you need to
be a member of <https://github.com/metalhelix> to view.

<http://tracks.stowers.org> is "a url-shortner and host for genomic
track files". Track file content is hosted on outward-facing server so
it might be rendered in the ucsc genome browser.  There is no hard
requirement that this content in fact be 'tracks', but, in practice it
is.  The url shortener is database-backed, allowing short & sweet URLs
to stand in for the typically LONG paths to the track content.  The
use of the url shortening service is entirely optional.  The content
is generally hidden from directory browsing and from indexing by
robots.

Tracks is a django application running under nginx/uwsgi.

# Server Configuration

```{.bash}
sudo yum -y install python # if needed
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

+  uwsgi (recent source <http://uwsgi-docs.readthedocs.org/en/latest/>)

NB: it is NOT installed inside the venv but rather with the system
python.  ALL OTHER python packages are installed inside the venv.

```{.bash}
pip install uwsgi
```
# Configure

TODO?: put the configuration files under source control.

## nginx - the webserver

webserver: nginx runs as user nginx

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
OWNER=deployer
NAME=uwsgi
DESC=uwsgi
TRACKS_WSGI=/microarray/tracks/tracks/wsgi.py
VENV=/home/deployer/venv/

DAEMON_OPTS="--socket 127.0.0.1:8001 --wsgi-file ${TRACKS_WSGI} -M -t 30 -p 16 -b 32768 -d /var/log/$NAME.log --pidfile /var/run/$NAME/$NAME.pid --uid $OWNER --home=${VENV} --stats 127.0.0.1:9191"
DAEMON_OPTS+=" --env PRODUCTION=1"  # this had been missing.
```


## tracks application

+ is implemented in the folders tracks, roasted, static 
+ runs as a web app in wsgi as user 'deployer' with password
  c.f. /home/bioinfo/.passwords
+ connects to postgres as user: deployer with password:
c.f. /home/bioinfo/.passwords

## python libraries and `virtualenv`

Create `venv`, a python virtual env, in home directory of user
deployer.

```{.bash}
pip install --user virtualenv  ## install the virtualenv tool
cd $HOME
virtualenv venv               ## create a virtualenv for this project.
```
## install required packages INTO THE VIRTUAL ENVIRONMENT:

```{.bash}
source ./venv/bin/activate   # enter the virtual environment.
pip install -r requirements.txt # install list of python modules & version needed for this app. 
pip install psycopg2
pip install pysqlite		# needed when PRODUCTION is unset (developing and debugging)
deactivate
```

WARNING: __You need not install any python modules outside of this virtual environment.__

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


```{.bash}
source ./venv/bin/activate
python manage.py syncdb
deactivate
```

## the database content

Import previous tracks data into django (as had been exported (using
dumpdata) from previous version of tracks database)

 + previous tracks meta data had to be stream editted first (required
   changing the name of django model)


```{.bash}
sed -i tracks_redirect.json s/redirect.redirecthit/roasted.redirecthit/g tracks.json
cat tracks_redirect.json | sed 's/redirect.redirecthit/roasted.redirecthit/g' | sed 's/redirect.target/roasted.target/g' > new_tracks.json

source ./venv/bin/activate
python manage.py loaddata ../new_tracks.json
deactivate
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

## Perform administrative taks with manage.py

+ [manage.py](https://docs.djangoproject.com/en/1.8/ref/django-admin/)
is a basic django command-line administration tool.
+ manage.py _MUST ALWAYS BE RUN WITHIN THE VIRTUAL ENVIRONMENT_, as
follows:

```{.bash}
source ./venv/bin/activate
python manage.py <subcommand>
deactivate
```

 + __ALWAYS MAKE SURE YOU RUN manage.py INSIDE VENV__
 + TODO?: Follow
[advice](http://stackoverflow.com/questions/3560225/django-not-finding-apps-in-virtualenv-when-using-manage-py-syncdb)
to ensure the virtual environment is always made available.


## Test application logic using development server

`python manage.py runserver` allows you to launch django application
using its built-in server (i.e. not under nginx/uwsgi).  This Allows
testing application isolated from web depolyment considerations (of
nginx and uwsgi services, permissions, logs, process ownership, etc).

This will run in using tracks.settings.production, which forces uses
postgres (live) database:

+ REMEMBER: _You must enter the virtual environment when using manage.py!!!_

```{.bash}
PRODUCTION=1 python manage.py runserver
```

You can instead run using tracks.settings.dev (i.e. using
(development) sqlite3) database (and also with DEBUG=TRUE)

```{.bash}
PRODUCTION= python manage.py runserver
````

Setting `DEBUG=True` (as done by track.settings.dev), causes web pages
to render without css.  Not pretty. Addtionally providing --insecure
option "allow(s) serving static files even with DEBUG=True" (as set in
settings.dev):

```{.bash}
PRODUCTION= python manage.py runserver --insecure
````
## stop and restart relevant services

```{.bash}
sudo /sbin/service uwsgi stop && sudo /sbin/service nginx stop && sudo /sbin/service uwsgi start && sudo /sbin/service nginx start
```

## create/update deployed schema to agree with django application model.

```{.bash}
PRODUCTION=1 python manage.py syncdb
```
## move a copy of production data into development sqlite

```{.bash}
PRODUCTION=1 python manage.py dumpdata --indent 1 > dumpdata_PRODUCTION.json
PRODUCTION=  python manage.py loaddata dumpdata_PRODUCTION.json
```

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

# RESOLVED ISSUES

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



# OPEN ISSUES

## configuration details are not backed up

Should we back up or copy somewhere the details configuration files?

## resolve remaining permissions/logfile

email to Jenny:

I think the ownership on /var/log/nginx/* and
/etc/nginx/logs/nginx/log/access.log is incorrect.

Can you remind me why we changed them to be owned by deployer earlier
in this thread?  Any good reason?

I think they probably need to owned by user nginx since the web worker
processes are running as user nginx.

As a result the access log is empty.

If you agree, would you change them please:

    chown -R nginx /var/log/nginx /etc/nginx/logs/nginx/log/access.log

and make the corresponding changes to /etc/logrotate.d/nginx

And, if you agree, while you’re editing the logrotate, you should
change the path to the nginx.pid file as well (which you will note is
owned by root).  If we don’t change it, then log rotation will cause
subsequent nginx logging to fail.

I think having logs owned by deployer makes sense for the uswgi logs
since that process IS running as user deployer.  But not the nginx
logs.  Do you agree?

Regarding this, I cannot see where the nginx uid/user is set.  The
‘user’ configuration directive in ‘nginx.conf’ (which would set it to
www-data) is commented out.  And the documentation I am seeing says
the default is ‘nobody’.  Do you know where this is set?  And, did you
have to create a user named nginx?

I am reviewing all this in the context of the deployed processes begin
split between nginx (for the web) and deployer (for the app).  If you
find a good write-up on how this should generally be done, I’d like to
see it.  I think some of our problems stem from this, and some from
having relocated some of the log files.

FYI: Uswgi also creates logs.  They should be rotated too.  Uwsgi has
its own built in log rotation scheme which can be enabled by adding
`--log-maxsize 100000000` to DAEMON_OPTs.  But think this is going to
pose a problem since regardless of how implemented, logrotation will
need to create a new file in /var/log but deployer lacks permisions
for this.  Should we `mkdir /var/log/uwsgi` owned by deployer and put
the log(s) there?

## confirm process managemnet practice with Jenny

Finally, you wrote earlier:

    /sbin/service nginx stop
    /sbin/service uwsgi stop
    /sbin/service uwsgi start
    /sbin/service nginx start

"Don't use sudo in front of these commands."

I think that this is wrong, at least it is wrong now, since they are
currently being run as root (i.e. during boot), you MUST you sudo.  Do
you agree?


## share this project repo with Jenny

Jenny -perhaps you cannot see it there since it is ‘private’.  Can
you?  If not, should we get you a membership to the metalhelix github
group?  I think so.  Do you?  If so, do you already have a personal
github account which we can put into the group?
