# encoding: utf-8
import os
import sys
from random import choice
from string import lowercase

TERM_ENCODING = getattr(sys.stdin, 'encoding', None)
PROMPT_PREFIX =  '> '

def extensions():
    extensions = []
    for file in os.listdir("./extensions"):
        if file.endswith(".py") and file not in ("__init__.py", "cache.py"):
           extensions.append(file.replace(".py", ""))
    return extensions

class ValidationError(Exception):
    """Raised for validation errors."""

def boolean(x):
    if x.upper() not in ('Y', 'YES', 'N', 'NO'):
        raise ValidationError("Please enter either 'y' or 'n'.")
    return x.upper() in ('Y', 'YES')

def ok(x):
    return x

def choices(*l):
    def val(x):
        if x not in l:
            raise ValidationError('Please enter one of %s.' % ', '.join(l))
        return x
    return val

def nonempty(x):
    if not x:
        raise ValidationError("Please enter some text.")
    return x

def do_prompt(d, key, text, default=None, validator=nonempty):
    while True:
        if default:
            prompt = PROMPT_PREFIX + '%s [%s]: ' % (text, default)
        else:
            prompt = PROMPT_PREFIX + text + ': '
        if sys.version_info < (3, 0):
            # for Python 2.x, try to get a Unicode string out of it
            if prompt.encode('ascii', 'replace').decode('ascii', 'replace') \
                    != prompt:
                if TERM_ENCODING:
                    prompt = prompt.encode(TERM_ENCODING)
                else:
                    print('* Note: non-ASCII default value provided '
                                    'and terminal encoding unknown -- assuming '
                                    'UTF-8 or Latin-1.')
                    try:
                        prompt = prompt.encode('utf-8')
                    except UnicodeEncodeError:
                        prompt = prompt.encode('latin1')
        x = raw_input(prompt).strip()
        if default and not x:
            x = default
        if not isinstance(x, unicode):
            # for Python 2.x, try to get a Unicode string out of it
            if x.decode('ascii', 'replace').encode('ascii', 'replace') != x:
                if TERM_ENCODING:
                    x = x.decode(TERM_ENCODING)
                else:
                    print('* Note: non-ASCII characters entered '
                                    'and terminal encoding unknown -- assuming '
                                    'UTF-8 or Latin-1.')
                    try:
                        x = x.decode('utf-8')
                    except UnicodeDecodeError:
                        x = x.decode('latin1')
        try:
            x = validator(x)
        except ValidationError, err:
            print('* ' + str(err))
            continue
        break

    d[key] = x


def ask_user(d):
    """Ask the user for quickstart values missing from *d*.

    Values are:

    * TITLE:     Title for the wiki
    * PRIVATE:   sets the wiki to be public or private 
    * MARKUP:    markup language choice
    * EXTENSIONS: Extensions to be included 
    """

    print('Welcome to the waliki %s quickconfig utility.') 
    print '''
Please enter values for the following settings (just press Enter to
accept a default value, if one is given in brackets).'''

    d['SECRET_KEY'] = "".join(choice(lowercase) for i in range(20)) 

    if 'PRIVATE' not in d:
        print 'Do you want you want a Private Waliki?'
        do_prompt(d, 'PRIVATE', 'Private (y/N)', 'n', boolean)

    if 'TITLE' not in d:
        print 'you should set a title for your Waliki.'
        do_prompt(d, 'TITLE', 'Waliki Title', 'Waliki Demo', ok)
    if 'MARKUP' not in d:
        print '''Choice a Markup Language, you can pick between 
restructuredtext or markdown'''
        do_prompt(d, 'MARKUP','Markup Language', 'restructuredtext', 
                  choices('restructuredtext', 'markdown'))

    if 'EXTENSIONS' not in d:
        print 'Choice the extensions that you want on your Waliki.'
        e = {}
        d['EXTENSIONS'] = []
        for extension in extensions():
            do_prompt(e, extension, '%s (y/N)'%extension, 'n', boolean)
            if e[extension]:
                d['EXTENSIONS'].append(extension)

def write_file(fpath, content):
    print 'Creating file %s.' % fpath
    f = open(fpath, 'w')
    try:
        f.write(content)
    finally:
        f.close()
    

def main():
    TARGET = os.path.join('content', 'config.py')
    if os.path.exists(TARGET):
	print "A config file already exists in %s" % TARGET
	return 
    d = {}
    try:
        ask_user(d)
    except (KeyboardInterrupt, EOFError):
        print
        print '[Interrupted.]'
        return
    print d
    #Make the content Dir
    if not os.path.exists('content'):
        os.makedirs('content')
    content = "# encoding: utf-8\n"
    for key, value in d.items():
        content += key + ' = ' + repr(value) 
        content +='\n'

    write_file(TARGET, content)

if __name__ == "__main__":      
    main()

