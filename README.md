Fetch AWS MFA accounts and security keys from [Chrome](https://www.google.com/chrome/) using [Selenium for Python](https://selenium-python.readthedocs.io/).


## Prerequisites

In order to build **mfakeys** you need to have [Python 2.7](https://www.python.org/download/releases/2.7/),
[Virtualenv](https://virtualenv.pypa.io/en/latest/) and
[GNU Make](http://www.gnu.org/software/make/) installed.

## Build
Creates standalone executable without any dependencies

<pre>
$ git clone https://github.com/ten0s/mfakeys.git
$ cd mfakeys
$ make
</pre>

## Usage

### General help
<pre>
$ dist/mfakeys -h
</pre>

### Print all AWS accounts (no account privided)
<pre>
$ dist/mfakeys -u USERNAME -p PASSWORD -c CODE --url URL
</pre>

### Print AWS keys for an account
<pre>
$ dist/mfakeys -u USERNAME -p PASSWORD -c CODE -a ACCOUNT --url URL
</pre>

### Resource file
<pre>
$ cat ~/.mfakeysrc
[default]
username=USERNAME
password=PASSWORD
url=URL
$ dist/mfakeys -c CODE -a ACCOUNT
</pre>
