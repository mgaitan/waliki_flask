

The "Git" backend
=================


The ``Git`` extension converts your content folder in a git repository, and make a commit on each edition.

With this simple logic you get:

* History of changes (who, when, what)
* Diff: compare any version an see what was added or removed
* See an old version of a page and restore it if you want (without loose history)
* restore deleted pages (not yet accessible via web but you can just go to ``/content`` and run ``$ git checkout -- *``)
* Fancy relative datetimes out of the box
* Simple stats: how many lines were added or removed. (go to the history page to see it in action!)
* Backup (pushing your repo to a remote place)
* Edit your content outside the web using the editor you prefer!

Also would be possible:

- Alert about conflicts (concurrent edition),
- merge versions
- more ideas?

.. tip::

   See https://github.com/mgaitan/waliki/blob/master/extensions/Git.py for the implementation

Few lines of code were taken from Naoki Okamura's Gily_ project.

.. _Gily: https://github.com/nyarla/gily

