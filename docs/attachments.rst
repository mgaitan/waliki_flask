.. tags: extensions

Extension "Attachments"
=======================

This extensions allow to upload files to a page and include in the text as an embedded image or inline link.

Go to edit this page, click othe button ``Attachments`` and try upload something and insert in the page.

For example, these are me and my niece :)

.. image:: /attachments/_attachment/974471_167677233415256_1026236323_n.jpg

.. tip::

   The code is at https://github.com/mgaitan/waliki/blob/master/extensions/uploads.py
   and the template (with the fancy javascript) here https://github.com/mgaitan/waliki/blob/master/templates/upload.html

On old-fashion browsers without FormData_ support (i.e. Internet Explorer < 10) the ajaxified upload form (including the uploading progress bar) degrades to a popup window.


.. FormData: https://developer.mozilla.org/en-US/docs/Web/API/FormData