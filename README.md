amavisdlogsumm
==============

amavisdlogsumm is a log analyzer/summarizer for [AMaViSd-new][1].

Since I am using [pflogsumm][2] to get a report of my Postfix logs, and I like it so much, I decided to fashon a similar script for amavisd-new. That is why it is named amavisdlogsum. However, I prefer Python over Perl.

The following packages were installed and used on [Ubuntu Server 14.04 LTS][3] to create this script:

* postfix: Version: 2.11.0-1
* amavisd-new: Version: 1:2.7.1-2ubuntu3

Everything was setup using [PostfixAmavisNew][4] from the Ubuntu Community Help Wiki.

Usage
=====

```
$ ./amavisdlogsumm.py -h
usage: amavisdlogsumm.py [-h] [-d {today,yesterday}] [--startup-detail]
                        logfiles [logfiles ...]

amavisdlogsumm.py - Produce AMaViSd-new logfile summary

positional arguments:
  logfiles

optional arguments:
  -h, --help            show this help message and exit
  -d {today,yesterday}, --day {today,yesterday}
  --startup-detail

$ sudo ./amavisdlogsumm.py -d today /var/log/mail.log
```

[1]: http://www.amavis.org/                             "amavisd-new"
[2]: http://jimsun.linxnet.com/postfix_contrib.html     "JIMSUN Postfix Contribs"
[3]: http://www.ubuntu.com/server                       "Ubuntu Server"
[4]: https://help.ubuntu.com/community/PostfixAmavisNew "Postfix Amavis-new"
