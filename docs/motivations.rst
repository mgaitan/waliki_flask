Motivations
===========

 In june of 2013 I've tweeted this:

.. raw:: html

   <blockquote class="twitter-tweet"><p>Is there any wiki engine that uses <a href="https://twitter.com/search?q=%23restructuredText&amp;src=hash">#restructuredText</a> as its core markup? Everything I found are incomplete or not working hacks</p>&mdash; Martín Gaitán (@tin_nqn_) <a href="https://twitter.com/tin_nqn_/statuses/350238674803363842">June 27, 2013</a></blockquote><script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

When our master `Roberto Alsina`_ offers to convert Alva_ in a wiki someday I asked him this:

.. _Roberto Alsina: http://www.ralsina.com.ar
.. _Alva: http://donewithniko.la/

.. raw:: html

   <blockquote class="twitter-tweet"><p><a href="https://twitter.com/tin_nqn_">@tin_nqn_</a> sure: <a href="https://t.co/Z377dGfw88">https://t.co/Z377dGfw88</a></p>&mdash; Roberto Alsina (@ralsina) <a href="https://twitter.com/ralsina/statuses/350247679168745475">June 27, 2013</a></blockquote><script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

That was the very beginning. Then few our per day in one week working.

In my original `pull request to Alex <https://github.com/alexex/wiki/pull/30>`_ I explained few motivations:


    I've researched a while looking for a simple yet usable wiki engine with support for restructuredtext, due it's what I write fluently and what I can use to render with Sphinx (de facto standard documentation tool in the python ecosystem), rst2pdf or whatever

    Few wikis like MoinMoin or the builtin wiki in Trac has this feature, but processing a "block of restructuredtext" in the middle of another core markup.

    Even when this project uses markdown, it's so simple to refactor this "render function" as a config option.

In fact, give rst support was very easy. ¡Thanks Roberto!

