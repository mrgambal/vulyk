Crowdsourcing platform for NLP tasks
====================================

.. image:: https://badge.fury.io/py/ner_trainer.png
    :target: http://badge.fury.io/py/ner_trainer

.. image:: https://travis-ci.org/mrgambal/ner_trainer.png?branch=master
        :target: https://travis-ci.org/mrgambal/ner_trainer

.. image:: https://pypip.in/d/ner_trainer/badge.png
        :target: https://pypi.python.org/pypi/ner_trainer

License
-------

-  Free software: BSD license
-  Documentation: https://ner\_trainer.readthedocs.org.

What is it?
-----------

We have results produced by different NLP software that should be
checked and verified manually. So, we decided to generalize those tasks
a bit and build a platform with basic support for crowdsourcing using
knowledge and chunks of code from the `unshred.it <http://unshred.it>`__
project. We don't use anything extraordinary: Flask, MongoDB, Bootstrap,
jQuery etc (all trademarks are the property of their respective owners,
don't forget that).

What for?
---------

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
procrastination-addicted) person could spent some time checking
correctness of NLP software processing results. Site will show you, mr.
Solver, random text, which was processed by one of our NER solutions,
with layered marks, that should highlight entities, extracted by our
software, and their types. If you see that something is wrong with
recognition you're able to:

-  Delete false positive entities (i.e those where NER tagging software
   thinks it’s an entity but it’s not).
-  Change boundary of the entity (i.e entity found only covers a part of
   a real one or entity found includes real one + neighbour words which
   aren’t a part of real one)
-  Create new entities in a given text (i.e entity hasn’t been found by
   a NER tagging software).
-  Provide free-form feedback to the author of the software.

In the best case we'll add some gamification (badges, achievement... you
name it).

How could I participate?
------------------------

You just need to contact me mr_gambal@outlook.com or [@dchaplinsky] via
chaplinsky.dmitry@gmail.com. One day we'll find one brave heart who'll
create a list of issues so the process will besimplified. But not now...

Example data
------------

To start developing you'll need a bootstrap data to work with. So...
**`Here <http://goo.gl/fLxQef>`__** is it - 7zipped json files (circa 15
MB).

It must be loaded into your MongoDB using:

.. code:: bash

    ./cli.py db load <path_to_extracted_files>/*.json

