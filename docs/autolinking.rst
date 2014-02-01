.. tags: waliki internals

How autolinking works
=====================

There is autolininking support for restructuredtext with a very simple trick: if you don't define the target in a link (a word ending with and undercore like ``this_``), it will automatically point to an internal wiki page (even if it doesn't exists yet).

So, just mark your links as ``somewhere_`` and get links to somewhere_

How it is implemented?
----------------------

It's dirty but very simple: Just render the page as usual using docutils and every unreferenced target is parsed and appendend to internals urls.

See the patch_ for details:

.. _patch: https://github.com/mgaitan/waliki/commit/3341a8f92dc3da78
