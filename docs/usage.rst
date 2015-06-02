=====
Usage
=====

To use Vulyk in a project::

    from vulyk.app import app

	if __name__ == '__main__':
	    app.config.from_object('local_settings')
	    app.run(host='0.0.0.0', port=5000)

As long as we use ``python-social-auth`` in vulyk you have to specify 
credentials for some auth providers supported::

	-*- coding: utf8 -*-
	SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '<your key here>'
	SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '<your secret here>'

	SOCIAL_AUTH_TWITTER_KEY = '<your key here>'
	SOCIAL_AUTH_TWITTER_SECRET = '<your secret here>'

	SOCIAL_AUTH_FACEBOOK_KEY = '<your key here>'
	SOCIAL_AUTH_FACEBOOK_SECRET = '<your secret here>'

	SOCIAL_AUTH_VK_OAUTH2_KEY = '<your key here>'

Needless to say that your settings must contain a dict of plugins (task types) 
you allow::

	ENABLED_TASKS = {
	    "vulyk_declaration": "DeclarationTaskType"
	}

Two more options may be put in in case if want to use Flask-Collect alongside 
with Flask-Assets capabilities to get all your static files collected in single
directory::

	# path to the directory you want to get static collected in
	COLLECT_STATIC_ROOT = "/var/lib/www-data/vulyk-static"
	# our own Storage for Flask-Collect. Allows collecting files from plugin
	# subfolders.
	COLLECT_STORAGE = 'vulyk.ext.storage'


Import data
-----------

Data loading that's been created to add some life to your plugin should be
performed via embedded CLI tool.
To plug CLI into an application I create file with similar content::

	#!/usr/bin/env python
	from vulyk.control import cli

	if __name__ == '__main__':
	    cli()

Having that done we're able to load tasks from datafiles (also supports gzip 
and bz2 archives with data). Datafile should contain a bunch of valid 
JSON-objects with arbitary content with line-separators in between.
Loading process may be initiated by calling::

	./control.py db load <task type> --batch "<batch_name>" <name or wildcard>.js
	# or
	./control.py db load <task type> --batch "<batch_name>" <name or wildcard>.bz2
	# or
	./control.py db load <task type> --batch "<batch_name>" <name or wildcard>.gz

Task type – is an internal name of type that will be assigned to your tasks.
Batch describes just a category of tasks you may want to be in there to 
simplify management and stats collecting (optional). You could omit batch name,
thus all tasks you load will get 'default' batch specified in settings.
