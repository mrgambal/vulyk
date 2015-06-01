Crowdsourcing platform for various tasks
====================================

.. image:: https://badge.fury.io/py/vulyk.png
    :target: http://badge.fury.io/py/vulyk

.. image:: https://travis-ci.org/mrgambal/vulyk.png?branch=master
        :target: https://travis-ci.org/mrgambal/vulyk

.. image:: https://pypip.in/d/vulyk/badge.png
        :target: https://pypi.python.org/pypi/vulyk

.. image:: https://readthedocs.org/projects/vulyk/badge/?version=latest
        :target: https://vulyk.readthedocs.org/en/latest/


License
-------

-  Free software: BSD license
-  Documentation: https://vulyk.readthedocs.org.

What is it?
-----------

We have a lot of tasks that can only be done manually. 
Those includes digitizing of scanned assets declarations, 
manual verification of results produced by different NLP software, stalking and so on.
So, we decided to generalize those tasks a bit and build a platform with basic support for crowdsourcing using
knowledge and chunks of code from the `unshred.it <http://unshred.it>`__
project. We don't use anything extraordinary: Flask, MongoDB, Bootstrap,
jQuery etc (all trademarks are the property of their respective owners,
don't forget that).

What for?
---------

-  digitize assets declarations of ukrainian officials for `Declarations project <http://declarations.com.ua>`__
-  improve the current state of Ukrainian NLP by creating a simple and
   robust solution for various NLP tasks that require human input.
-  process and manually verify existing results from
   `PullEnti <http://pullenti.ru>`__ (by Konstantin Kuznetsov) and
   morphological analyzer (by Andriy Rysin, Mariana Romanyshyn, et al.).
-  build tagged corpora of different kinds using manually processed
   results.
-  for the sake of The Great Justice of course!

But, God, how?
--------------

We provide some kind of playground where any interested (or
procrastination-addicted) person could spent some time doing some manual tasks. 
Site will show you, mr. Solver, some tasks of a given type, which you'll need to solve

In the best case we'll add some gamification (badges, achievement... you
name it).

Leaderboard is already in place!

How could I participate?
------------------------

You just need to contact me mr_gambal@outlook.com or `@dchaplinsky <http://github.com/dchaplinsky>`__ via
chaplinsky.dmitry@gmail.com. One day we'll find one brave heart who'll
create a list of issues so the process will besimplified. But not now...

Running it locally
------------
TBA

.. code:: bash

    venv

