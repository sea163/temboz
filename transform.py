# filtering regular expressions, used to strip out annoyances like ads,
# web bugs and the like from feeds
import re, degunk

# uncomment this if you have made changes to the degunk module
# reload(degunk)

filter_list = [
  # don't mess with breaks
  degunk.Re('(<br\s+[^>]*>)', 0, '<br>'),
  # Blegs
  degunk.Re('<a href="http://www.bloglines.com/sub/.*?</a>'),
  degunk.Re('<a href="http://del.icio.us/post.*?</a>'),
  degunk.Re('<a href="http://digg.com/submit.*?</a>'),
  degunk.Re('<a href="http://www.furl.net/storeIt.jsp.*?</a>'),
  degunk.Re('<a href="http://ma.gnolia.com/bookmarklet/add.*?</a>'),
  degunk.Re('<a href="http://www.propeller.com/submit.*?</a>'),
  degunk.Re('<a href="http://reddit.com/submit.*?</a>'),
  degunk.Re('<a href="http://www.sphere.com/search\\?q=sphereit.*?</a>'),
  degunk.Re('<a href="http://www.stumbleupon.com/submit.*?</a>'),
  degunk.Re('<a href="http://tailrank.com/share/.*?</a>'),
  degunk.Re('<a href="http://technorati.com/faves\\?add.*?</a>'),
  degunk.Re('<a href="http://www.feedburner.com/fb/a/emailFlare.*?</a>'),
  degunk.Re('<a href="http://slashdot.org/bookmark.pl.*?</a>'),
  degunk.Re('<a href="http://www.facebook.com/share.php.*?</a>'),
  degunk.Re('<a href="http://www.google.com/bookmarks/mark.*?</a>'),
  # Feedburner ads
  degunk.Re('<a href[^>]*><img src="http://feeds.feedburner[^>]*></a>'),
  degunk.Re('<p><a href="(http://feeds\\.[^"/>]*/~./)[^"]*">'
            '<img src="\\1[^>]*></a></p>'),
  # Feedburner web bug
  degunk.Re('<img src="http://feeds.feedburner.com.*?/>'),
  # web bugs dumb enough to reveal themselves
  degunk.Re('<img[^>]*width="1"[^>]*height="1"[^>]*>'),
  degunk.Re('<img[^>]*height="1"[^>]*width="1"[^>]*>'),
  # Google ads
  degunk.Re('<a[^>]*href="http://imageads.googleadservices[^>]*>'
            '[^<>]*<img [^<>]*></a>', re.MULTILINE),
  degunk.Re('<a[^>]*href="http://www.google.com/ads_by_google[^>]*>[^<>]*</a>',
            re.MULTILINE),
  degunk.Re('<p><map[^>]*><area[^>]*href="http://imageads.google.*?</p>',
            re.MULTILINE),
  # Falk AG ads
  degunk.Re('<div><br>\s*<strong>.*?<a href="[^"]*falkag.net[^>]*>.*?</strong>'
            '<br>.*?</div>', re.IGNORECASE + re.DOTALL),
  degunk.Re('<a href="[^"]*falkag.net[^>]*><img[^>]*></a>'),
  # Empty paragraphs used as spacers in front of ads
  degunk.Re('<p>&#160;</p>'),
  degunk.Re('<p><br />\s*</p>\s*', re.MULTILINE),
  # DoubleClick ads
  degunk.Re('<a[^>]*href="http://ad.doubleclick.net[^>]*>.*?</a>',
            re.MULTILINE),
  degunk.Re('<p>ADVERTISEMENT.*?</p>'),
  # Yahoo ads
  degunk.Re('<p class="adv">.*?</p>'),
  # annoying forms inside posts, e.g. Russell Beattie
  degunk.Re('<form.*?</form>', re.IGNORECASE + re.DOTALL),
  # Weblogs Inc, ads
  degunk.Re('<p><a[^>]*href="http://feeds.gawker.com[^>]*>[^<>]*'
            '<img [^>]*src="http://feeds.gawker.com[^<>]*></a></p>',
            re.MULTILINE),
  # annoying Weblogs Inc. footer
  degunk.Re('<h([0-9])></h\1>'),
  degunk.Re('<a href=[^>]*>Permalink</a>.*?<a [^>]*>'
            'Email this</a>.*?Comments</a>',
            re.IGNORECASE + re.DOTALL),
  degunk.Re('<p><font size="1"><hr />SPONSORED BY.*?</p>'),
  # Engadget ads
  degunk.Re('<hr /><p>SPONSORED BY.*?</p>\s*', re.MULTILINE),
  # Gawker cross-shilling
  degunk.Re('&nbsp;<br><a href=[^>]*>Comment on this post</a>\s*<br>Related.*',
            re.IGNORECASE + re.DOTALL),
  degunk.Re('<div class="feedflare">.*?</div>', re.IGNORECASE + re.DOTALL),
  # Pheedo ads
  degunk.Re('<p><a href="http://www.pheedo.*?</p>', re.MULTILINE + re.DOTALL),
  degunk.Re('<div><a href="http://www.pheedo[^"]*">\s*'
            '<img src="http://www.pheedo.com.*?</div>',
            re.MULTILINE + re.DOTALL),
  degunk.Re('<a href="http://[^"]*.pheedo[^"]*">\s*'
            '<img [^>]*src="http://www.pheedo.com.*?</a>',
            re.MULTILINE + re.DOTALL),
  # Broken Pheedo links for IEEE Spectrum
  degunk.ReUrl(url=r'http://pheedo.com\1',
               regex_url=r'http://www.pheedo.com(.*)'),
  # Mediafed ads
  degunk.Re('<br><a href="http://[^"]*.feedsportal.com/[^"]*"><img border="0" '
            'src="http://[^"]*.feedsportal.com[^"]*" /></a>'),
  # IDFuel URLs should point to full article, not teaser
  degunk.ReUrl(url=r'http://www.idfuel.com/index.php?p=\1&more=1',
               regex_url=r'http://www.idfuel.com/index.php\?p=([0-9]*)'),
  # Strip The Register redirection that causes link_already() to fail
  degunk.ReUrl(
    url=r'\1', regex_url=r'http://go.theregister.com/feed/(http://.*)'),
  # Same for I Cringely
  degunk.ReUrl(
  url=r'http://www.pbs.org/cringely/\1',
  regex_url=r'http://www.pbs.org/cringely/rss1/redir/cringely/(.*)'),
  # Register ads
  degunk.Re('<strong>Advertisement</strong><br>'),
  # Inquirer blegging
  degunk.Re('<div class="mf-viral">.*</div>'),
  # Salon ads
  degunk.Re('<p><a href="http://feeds.salon.com/~a[^>]*><img '
            '[^>]*></a></p><img[^>]*>'),
  # bypass Digg
  degunk.Dereference('digg.com', '<h3 id="title1"><a href="([^"]*)"'),
  # DoubleClick ads
  degunk.Re('<a href="http://[^"]*doubleclick.*?</a>',
            re.MULTILINE + re.DOTALL),
  # If I want to share, I can do it myself, thanks
  degunk.Re('<p class="akst_link">.*?</p>', re.MULTILINE + re.DOTALL),
  # Daily Python URL should link to actual articles, not to itself
  degunk.UseFirstLink('http://www.pythonware.com/daily/'),
  degunk.ReTitle('\\1', '<div class="description">.*?<a href=.*?>(.*?)</a>',
                 re.MULTILINE + re.DOTALL),
  # Inquirer clutter
  degunk.Re('<p><small>[^<>]*<a href="http://www.theinquirer.net[^<>]*><i>'
            '[^<>]*Read the full article.*', re.MULTILINE + re.DOTALL),
  degunk.Re('<p><small>[^<>]*<a href="http://www.theinquirer.net.*?<i>',
            re.MULTILINE),
  # possibly caused by bugs in feedparser
  degunk.Re('<br>[.>]<br>', 0, '<br>', iterate=True),
  # unwarranted multiple empty lines
  degunk.Re('<br>(<br>)+', 0, '<br>'),
  # junk
  degunk.Re('<strong></strong>', 0, ''),
  # unwarranted final empty lines
  degunk.Re('(<br>)+$'),
  ]
