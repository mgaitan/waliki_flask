.. tags: waliki internals


Write an extension
==================

Waliki has a very little core designed to be extensible with **plugins** (or, following the Flask jargon, *extensions*).

At the moment, there are only two extensions available (`Git </git-backend>`_ and `rst2pdf </get-as-pdf>`_) but you can create a new one very easily.

An extension is a simple python module with the only requirement of define a function named ``init()`` that receive the ``app`` instance as paramenter.

How to activate an extension?
------------------------------

Considering it is in ``extensions/yours.py`` just append ``yours`` in the ``EXTENSIONS`` config var.  For example, to activate this and the git one, it will looks like this::

    EXTENSIONS = ['Git', 'yours']

Extend what?
----------------


.. tip:: As frequent in early stages of a project, the best documentation is the code.
         See https://github.com/mgaitan/waliki/blob/master/extensions/Git.py for the
         best example of everything mentioned in this page.


An extensions can do many things.

Connect to signals
++++++++++++++++++

For example, connect receivers functions to the signals Waliki send when few actions happen. At the moment there is two:

* ``page_saved`` is sent just after save a page. The parameters are the
  ``page``instance, the ``user`` who edit the page,  and
  the summary ``message`` . For example, Git extensions uses it to make a commit with the new comment.

* ``pre_display`` is send just before render a page with a dictionay ``extra_context``.
  that is passed to jinja. Git uses it to register ``extra_actions`` in the dropdown
  menu (i.e the link to page History).

.. note:: Of course, you can add any new signal you need!

Add views
+++++++++

Of course, you can add new views. To do this you need to create a Blueprint_ instance, that create the "namespace" to decorete for your views. Don't forget to register this blueprint in your ``init()`` function.

.. _Blueprint: http://flask.pocoo.org/docs/blueprints/

As a URL convention, we use ``/<path:url/_action[/other_parameters]`` as routing pattern. For example ``/home/_history`` or ``/home/_version/56fd4c5`` .


Extend existent views
++++++++++++++++++++++

Following the idea of Git and ``pre_display`` you can extend (or even override) the context of an existent view. Try to be a good citizen and to your things without affect others.

For example, if you want to register a new "extra_action" check if there is previous extra actiond and **append** yours. For example::

    def extra_actions(page, **extra):
        context = extra['extra_context']
        actions = context.get('extra_actions', [])
        actions.append(('History', url_for('gitplugin.history', url=page.url)))
        context['extra_actions'] = actions

Your turn
----------

Have and `idea </ideas>`_ ? Just add it to the list, and if you can code, fork the project and send us a PR!

