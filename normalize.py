# -*- coding: iso-8859-1 -*-
import sys, time, re, codecs, string, traceback, socket, HTMLParser, hashlib
import unicodedata, htmlentitydefs, urllib2, urlparse, html5lib
import feedparser, param, transform, util, porter2

# XXX TODO
#
# XXX normalize feed['title'] to quote &amp; &quot;
#
# XXX Many of these heuristics have probably been addressed by newer versions
# XXX of feedparser.py

#date_fmt = '%a, %d %b %Y %H:%M:%S %Z'
date_fmt = '%Y-%m-%d %H:%M:%S'

# strip out class attributes from articles
feedparser._HTMLSanitizer.acceptable_attributes.remove('class')

# strip diacritics. Unicode normalization form D (NFD) maps letters with
# diacritics into the base letter followed by a combining diacritic, all
# we need to do is get rid of the combining diacritics
# this probably does not work with exotic characters like
# U+FDF2 (Arabic ligature Allah)
def stripc(c):
  return unicodedata.normalize('NFD', c)[0]
def strip_diacritics(s):
  return u''.join(map(stripc, s))

stop_words = ['i', 't', 'am', 'no', 'do', 's', 'my', 'don', 'm', 'on',
              'get', 'in', 'you', 'me', 'd', 've']
# list originally from: http://bll.epnet.com/help/ehost/Stop_Words.htm
stop_words += ['a', 'the', 'of', 'and', 'that', 'for', 'by', 'as', 'be',
'or', 'this', 'then', 'we', 'which', 'with', 'at', 'from', 'under',
'such', 'there', 'other', 'if', 'is', 'it', 'can', 'now', 'an', 'to',
'but', 'upon', 'where', 'these', 'when', 'whether', 'also', 'than',
'after', 'within', 'before', 'because', 'without', 'however',
'therefore', 'between', 'those', 'since', 'into', 'out', 'some', 'about',
'accordingly', 'again', 'against', 'all', 'almost', 'already',
'although', 'always', 'among', 'any', 'anyone', 'apparently', 'are',
'arise', 'aside', 'away', 'became', 'become', 'becomes', 'been', 'being',
'both', 'briefly', 'came', 'cannot', 'certain', 'certainly', 'could',
'etc', 'does', 'done', 'during', 'each', 'either', 'else', 'ever',
'every', 'further', 'gave', 'gets', 'give', 'given', 'got', 'had',
'hardly', 'has', 'have', 'having', 'here', 'how', 'itself', 'just',
'keep', 'kept', 'largely', 'like', 'made', 'mainly', 'make', 'many',
'might', 'more', 'most', 'mostly', 'much', 'must', 'nearly',
'necessarily', 'neither', 'next', 'none', 'nor', 'normally', 'not',
'noted', 'often', 'only', 'our', 'put', 'owing', 'particularly',
'perhaps', 'please', 'potentially', 'predominantly', 'present',
'previously', 'primarily', 'probably', 'prompt', 'promptly', 'quickly',
'quite', 'rather', 'readily', 'really', 'recently', 'regarding',
'regardless', 'relatively', 'respectively', 'resulted', 'resulting',
'results', 'said', 'same', 'seem', 'seen', 'several', 'shall', 'should',
'show', 'showed', 'shown', 'shows', 'significantly', 'similar',
'similarly', 'slightly', 'so', 'sometime', 'somewhat', 'soon',
'specifically', 'strongly', 'substantially', 'successfully',
'sufficiently', 'their', 'theirs', 'them', 'they', 'though', 'through',
'throughout', 'too', 'toward', 'unless', 'until', 'use', 'used', 'using',
'usually', 'various', 'very', 'was', 'were', 'what', 'while', 'who',
'whose', 'why', 'widely', 'will', 'would', 'yet']
# French stop words
# list originally from: http://www.up.univ-mrs.fr/veronis/data/antidico.txt
# XXX it's not good practice to mix languages like this, we should use
# XXX feed language metadata and track what language a content is written in
# XXX but that would require significant data model changes
stop_words += [strip_diacritics(unicode(s, 'iso8859-15')) for s in [
  "a", "A", "�", "afin", "ah", "ai", "aie", "aient", "aies", "ailleurs",
  "ainsi", "ait", "alentour", "alias", "allais", "allaient",
  "allait", "allons", "allez", "alors", "Ap.", "Apr.", "apr�s",
  "apr�s-demain", "arri�re", "as", "assez", "attendu", "au", "aucun",
  "aucune", "au-dedans", "au-dehors", "au-del�", "au-dessous",
  "au-dessus", "au-devant", "audit", "aujourd'", "aujourd'hui",
  "auparavant", "aupr�s", "auquel", "aura", "aurai", "auraient",
  "aurais", "aurait", "auras", "aurez", "auriez", "aurions",
  "aurons", "auront", "aussi", "aussit�t", "autant", "autour", "autre",
  "autrefois", "autres", "autrui", "aux", "auxdites", "auxdits",
  "auxquelles", "auxquels", "avaient", "avais", "avait", "avant",
  "avant-hier", "avec", "avez", "aviez", "avions", "avoir", "avons",
  "ayant", "ayez", "ayons", "B", "bah", "banco", "b�", "beaucoup", "ben",
  "bien", "bient�t", "bis", "bon", "�'", "c.-�-d.", "Ca", "�a", "��",
  "cahin-caha", "car", "ce", "-ce", "c�ans", "ceci", "cela", "celle",
  "celle-ci", "celle-l�", "celles", "celles-ci", "celles-l�", "celui",
  "celui-ci", "celui-l�", "cent", "cents", "cependant", "certain",
  "certaine", "certaines", "certains", "certes", "ces", "c'est-�-dire",
  "cet", "cette", "ceux", "ceux-ci", "ceux-l�", "cf.", "cg", "cgr",
  "chacun", "chacune", "chaque", "cher", "chez", "ci", "-ci", "ci-apr�s",
  "ci-dessous", "ci-dessus", "cinq", "cinquante", "cinquante-cinq",
  "cinquante-deux", "cinquante-et-un", "cinquante-huit",
  "cinquante-neuf", "cinquante-quatre", "cinquante-sept",
  "cinquante-six", "cinquante-trois", "cl", "cm", "cm�", "combien",
  "comme", "comment", "contrario", "contre", "crescendo", "D", "d'",
  "d'abord", "d'accord", "d'affil�e", "d'ailleurs", "dans", "d'apr�s",
  "d'arrache-pied", "davantage", "de", "debout", "dedans", "dehors",
  "d�j�", "del�", "demain", "d'embl�e", "depuis", "derechef",
  "derri�re", "des", "d�s", "desdites", "desdits", "d�sormais",
  "desquelles", "desquels", "dessous", "dessus", "deux", "devant",
  "devers", "dg", "die", "diff�rentes", "diff�rents", "dire", "dis",
  "disent", "dit", "dito", "divers", "diverses", "dix", "dix-huit",
  "dix-neuf", "dix-sept", "dl", "dm", "donc", "dont", "dor�navant",
  "douze", "du", "d�", "dudit", "duquel", "durant", "E", "eh", "elle",
  "-elle", "elles", "-elles", "en", "'en", "-en", "encore", "enfin",
  "ensemble", "ensuite", "entre", "entre-temps", "envers", "environ",
  "es", "�s", "est", "et", "et/ou", "�taient", "�tais", "�tait", "�tant",
  "etc", "�t�", "�tes", "�tiez", "�tions", "�tre", "eu", "eue", "eues",
  "euh", "e�mes", "eurent", "eus", "eusse", "eussent", "eusses",
  "eussiez", "eussions", "eut", "e�t", "e�tes", "eux", "expr�s",
  "extenso", "extremis", "F", "facto", "fallait", "faire", "fais",
  "faisais", "faisait", "faisaient", "faisons", "fait", "faites",
  "faudrait", "faut", "fi", "flac", "fors", "fort", "forte", "fortiori",
  "frais", "f�mes", "fur", "furent", "fus", "fusse", "fussent", "fusses",
  "fussiez", "fussions", "fut", "f�t", "f�tes", "G", "GHz", "gr",
  "grosso", "gu�re", "H", "ha", "han", "haut", "h�", "hein", "hem",
  "heu", "hg", "hier", "hl", "hm", "hm�", "hol�", "hop", "hormis", "hors",
  "hui", "huit", "hum", "I", "ibidem", "ici", "ici-bas", "idem", "il",
  "-il", "illico", "ils", "-ils", "ipso", "item", "J", "j'", "jadis",
  "jamais", "je", "-je", "jusqu'", "jusqu'�", "jusqu'au", "jusqu'aux",
  "jusque", "juste", "K", "kg", "km", "km�", "L", "l'", "la", "-la", "l�",
  "-l�", "l�-bas", "l�-dedans", "l�-dehors", "l�-derri�re",
  "l�-dessous", "l�-dessus", "l�-devant", "l�-haut", "laquelle",
  "l'autre", "le", "-le", "lequel", "les", "-les", "l�s", "lesquelles",
  "lesquels", "leur", "-leur", "leurs", "lez", "loin", "l'on",
  "longtemps", "lors", "lorsqu'", "lorsque", "lui", "-lui", "l'un",
  "l'une", "M", "m'", "m�", "m�", "ma", "maint", "mainte", "maintenant",
  "maintes", "maints", "mais", "mal", "malgr�", "me", "m�me", "m�mes",
  "mes", "mg", "mgr", "MHz", "mieux", "mil", "mille", "milliards",
  "millions", "minima", "ml", "mm", "mm�", "modo", "moi", "-moi", "moins",
  "mon", "moult", "moyennant", "mt", "N", "n'", "nagu�re", "ne",
  "n�anmoins", "neuf", "ni", "n�", "non", "nonante", "nonobstant", "nos",
  "notre", "nous", "-nous", "nul", "nulle", "O", "�", "octante", "oh",
  "on", "-on", "ont", "onze", "or", "ou", "o�", "ouais", "oui", "outre",
  "P", "par", "parbleu", "parce", "par-ci", "par-del�", "par-derri�re",
  "par-dessous", "par-dessus", "par-devant", "parfois", "par-l�",
  "parmi", "partout", "pas", "pass�", "passim", "pendant", "personne",
  "petto", "peu", "peut", "peuvent", "peux", "peut-�tre", "pis", "plus",
  "plusieurs", "plut�t", "point", "posteriori", "pour", "pourquoi",
  "pourtant", "pr�alable", "pr�s", "presqu'", "presque", "primo",
  "priori", "prou", "pu", "puis", "puisqu'", "puisque", "Q", "qu'", "qua",
  "quand", "quarante", "quarante-cinq", "quarante-deux",
  "quarante-et-un", "quarante-huit", "quarante-neuf",
  "quarante-quatre", "quarante-sept", "quarante-six",
  "quarante-trois", "quasi", "quatorze", "quatre", "quatre-vingt",
  "quatre-vingt-cinq", "quatre-vingt-deux", "quatre-vingt-dix",
  "quatre-vingt-dix-huit", "quatre-vingt-dix-neuf",
  "quatre-vingt-dix-sept", "quatre-vingt-douze", "quatre-vingt-huit",
  "quatre-vingt-neuf", "quatre-vingt-onze", "quatre-vingt-quatorze",
  "quatre-vingt-quatre", "quatre-vingt-quinze", "quatre-vingts",
  "quatre-vingt-seize", "quatre-vingt-sept", "quatre-vingt-six",
  "quatre-vingt-treize", "quatre-vingt-trois", "quatre-vingt-un",
  "quatre-vingt-une", "que", "quel", "quelle", "quelles", "quelqu'",
  "quelque", "quelquefois", "quelques", "quelques-unes",
  "quelques-uns", "quelqu'un", "quelqu'une", "quels", "qui",
  "quiconque", "quinze", "quoi", "quoiqu'", "quoique", "R", "revoici",
  "revoil�", "rien", "S", "s'", "sa", "sans", "sauf", "se", "secundo",
  "seize", "selon", "sensu", "sept", "septante", "sera", "serai",
  "seraient", "serais", "serait", "seras", "serez", "seriez", "serions",
  "serons", "seront", "ses", "si", "sic", "sine", "sinon", "sit�t",
  "situ", "six", "soi", "soient", "sois", "soit", "soixante",
  "soixante-cinq", "soixante-deux", "soixante-dix",
  "soixante-dix-huit", "soixante-dix-neuf", "soixante-dix-sept",
  "soixante-douze", "soixante-et-onze", "soixante-et-un",
  "soixante-et-une", "soixante-huit", "soixante-neuf",
  "soixante-quatorze", "soixante-quatre", "soixante-quinze",
  "soixante-seize", "soixante-sept", "soixante-six", "soixante-treize",
  "soixante-trois", "sommes", "son", "sont", "soudain", "sous",
  "souvent", "soyez", "soyons", "stricto", "suis", "sur",
  "sur-le-champ", "surtout", "sus", "T", "-t", "t'", "ta", "tacatac",
  "tant", "tant�t", "tard", "te", "tel", "telle", "telles", "tels", "ter",
  "tes", "toi", "-toi", "ton", "t�t", "toujours", "tous", "tout", "toute",
  "toutefois", "toutes", "treize", "trente", "trente-cinq",
  "trente-deux", "trente-et-un", "trente-huit", "trente-neuf",
  "trente-quatre", "trente-sept", "trente-six", "trente-trois", "tr�s",
  "trois", "trop", "tu", "-tu", "U", "un", "une", "unes", "uns", "USD",
  "V", "va", "vais", "vas", "vers", "veut", "veux", "via", "vice-versa",
  "vingt", "vingt-cinq", "vingt-deux", "vingt-huit", "vingt-neuf",
  "vingt-quatre", "vingt-sept", "vingt-six", "vingt-trois",
  "vis-�-vis", "vite", "vitro", "vivo", "voici", "voil�", "voire",
  "volontiers", "vos", "votre", "vous", "-vous", "W", "X", "y", "-y",
  "Z", "z�ro"]]

stop_words = set(stop_words)

# translate to lower case, normalize whitespace
# for ease of filtering
# this needs to be a mapping as Unicode strings do not support traditional
# str.translate with a 256-length string
lc_map = {}
punct_map = {}
for c in string.whitespace:
  lc_map[ord(c)] = 32
del lc_map[32]
for c in string.punctuation + '\'\xab\xbb':
  punct_map[ord(c)] = 32
punct_map[0x2019] = u"'"

# decode HTML entities with known Unicode equivalents
ent_re = re.compile(r'\&([^;]*);')
def ent_sub(m):
  ent = m.groups()[0]
  if ent in htmlentitydefs.name2codepoint:
    return unichr(htmlentitydefs.name2codepoint[ent])
  if ent.startswith('#'):
    if ent.lower().startswith('#x'):
      codepoint = int('0x' + ent[2:], 16)
    else:
      try:
        codepoint = int(ent[1:])
      except ValueError:
        return ent
    if codepoint > 0 and codepoint < sys.maxunicode:
      return unichr(codepoint)
  # fallback - leave as-is
  return '&%s;' % ent
  
def decode_entities(s):
  return ent_re.sub(ent_sub, s)

# XXX need to normalize for HTML entities as well
def lower(s):
  """Turn a string lower-case, including stripping accents"""
  try:
    s = unicode(s)
  except UnicodeDecodeError:
    s = s.decode('utf8')
  return strip_diacritics(decode_entities(s)).translate(lc_map).lower()

# XXX this implementation is hopefully correct, but inefficient
# XXX we should be able to replace it with a finite state automaton in C
# XXX for better performance
# tested with u=u'\xe9sop\xe9sopfoo\xe9sop' and unicodedata.normalize('NFD', u)
def replace_first(s, pat, repl):
  """Case-insensitive replacement of the first occurrent of pat in s by repl"""
  lc = lower(s)
  pat = lower(pat)
  start = lc.find(pat)
  if start == -1:
    return s
  else:
    # find the beginning of the pattern in the original string
    # since we strip accent, the equivalent in the original string may be
    # further than in the lower-case version
    # i.e. we are assuming that len(lower(s)) <= len(s) for all Unicode s
    while not lower(s[start:]).startswith(pat):
      start += 1
    end = start + len(pat)
    while lower(s[start:end]) != pat:
      end += 1
    return s[:start] + repl + s[end:]

strip_tags_re = re.compile('<[^>]*>')
def get_words(s):
  return set([
    word for word
    in lower(unicode(strip_tags_re.sub('', unicode(s)))
             ).translate(punct_map).split()
    if word not in stop_words])
def stem(words):
  return {porter2.stem(word) for word in words}
  
########################################################################
# HTML tag balancing logic
#
# from the HTML4 loose DTD http://www.w3.org/TR/html4/loose.dtd
fontstyle = ('b', 'big', 'i', 's', 'small', 'strike', 'tt', 'u')
phrase = ('abbr', 'acronym', 'cite', 'code', 'dfn', 'em', 'kbd', 'samp',
          'strong', 'var')
heading = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
html4_elts = ('a', 'address', 'applet', 'area', 'base', 'basefont', 'bdo',
              'blockquote', 'body', 'br', 'button', 'caption', 'center',
              'col', 'colgroup', 'dd', 'del', 'dir', 'div', 'dl', 'dt',
              'fieldset', 'font', 'form', 'frame', 'frameset', 'head', 'hr',
              'html', 'iframe', 'img', 'input', 'ins', 'isindex', 'label',
              'legend', 'li', 'link', 'map', 'menu', 'meta', 'noframes',
              'noscript', 'object', 'ol', 'optgroup', 'option', 'p', 'param',
              'pre', 'q', 'script', 'select', 'span', 'style', 'sub', 'sup',
              'table', 'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead',
              'title', 'tr', 'ul') + fontstyle + phrase + heading
inline_elts = ('a', 'abbr', 'acronym', 'address', 'bdo', 'caption', 'cite',
               'code', 'dfn', 'dt', 'em', 'font', 'i',
               'iframe', 'kbd', 'label', 'legend', 'p', 'pre', 'q', 's',
               'samp', 'small', 'span', 'strike', 'strong', 'sub', 'sup',
               'tt', 'u', 'var') + fontstyle + phrase + heading
# strictly speaking the closing '</p> tag is optional, but let's close it
# since it is so common
closing = ('a', 'address', 'applet', 'bdo', 'blockquote', 'button', 'caption',
           'center', 'del', 'dir', 'div', 'dl', 'fieldset', 'font', 'form',
           'frameset', 'iframe', 'ins', 'label', 'legend', 'map', 'menu',
           'noframes', 'noscript', 'object', 'ol', 'optgroup', 'pre', 'q',
           'script', 'select', 'span', 'style', 'sub', 'sup', 'table',
           'textarea', 'title', 'ul') + fontstyle + phrase + heading + ('p',)
# <!ENTITY % block
block = ('address', 'blockquote', 'center', 'dir', 'div', 'dl', 'fieldset',
         'form', 'hr', 'isindex', 'menu', 'noframes', 'noscript', 'ol', 'p',
         'pre', 'table', 'ul') + heading
# for XSS attacks, as feedparser is not completely immune
banned = ('script', 'applet', 'style')
# speed up things a bit
block = set(block)
closing = set(closing)
banned = set(banned)

tag_re = re.compile(r'(<>|<[^!].*?>|<!\[CDATA\[|\]\]>|<!--.*?-->|<[!]>)',
                    re.DOTALL | re.MULTILINE)
def balance(html, limit_words=None, ellipsis=' ...'):
  if not limit_words:
    return html5lib.serialize(html5lib.parse(html))
  word_count = 0
  tokens = tag_re.split(html)
  out = []
  stack = []
  for token in tokens:
    if not token.startswith('<'):
      if limit_words and word_count > limit_words:
        break
      words = token.split()
      word_count += len(words)
      if limit_words and word_count > limit_words:
        crop = limit_words - word_count
        out.append(' '.join(words[:crop]) + ellipsis)
      else:
        out.append(token)
      continue
    if token.startswith('<!'): continue
    if token == ']]>': continue
    if not token.endswith('>'): continue # invalid
    element = token[1:-1].split()[0].lower()
    if not element: continue # invalid
    if element in banned:
      element = 'pre'
      token = '<pre>'

    if element.startswith('/'):
      element = element[1:]
      if element in banned:
        element = 'pre'
        token = '</pre>'
      if element in stack:
        top = None
        while stack and top != element:
          top = stack.pop()
          out.append('</%s>' % top)
        continue
      else:
        continue

    if element in block and stack and stack[-1] not in block:
      # close previous block if any
      for i in xrange(len(stack) - 1, -1, -1):
        if stack[i] in block: break
      stack, previous_block = stack[:i], stack[i:]
      previous_block.reverse()
      for tag in previous_block:
        out.append('</%s>' % tag)
      
    if element in closing and not token.endswith('/>'):
      stack.append(element)
    out.append(token)
  # flush the stack
  out.extend(['</%s>' % element for element in reversed(stack)])
  return ''.join(out)

########################################################################
def normalize_all(f):
  normalize_feed(f)
  for item in f.entries:
    normalize(item, f)

def normalize_feed(f):
  if 'description' not in f['channel']:
    f['channel']['description'] = f['channel'].get('title', '')
  if 'modified' in f and type(f['modified']) == str:
    try:
      f['modified'] = time.strptime(f['modified'],
                                    '%a, %d %b %Y %H:%M:%S GMT')
    except ValueError:
      f['modified'] = time.strptime(f['modified'],
                                    '%a, %d %b %Y %H:%M:%S +0000')

# Often, broken RSS writers will not handle daylight savings time correctly
# and use a timezone that is off by one hour. For instance, in the US/Pacific
# time zone:
# February 3, 2004, 5:30PM is 2004-02-03T17:30:00-08:00 (standard time)
# August 3, 2004, 5:30PM US/Pacific is 2004-08-03T17:30:00-07:00 (DST)
# but broken implementations will incorrectly write:
# 2004-08-03T17:30:00-08:00 in the second case
# There is no real good way to ward against this, but if the created or
# modified date is in the future, we are clearly in this situation and
# substract one hour to correct for this bug
def fix_date(date_tuple):
  if not date_tuple:
    return date_tuple
  if date_tuple > time.gmtime():
    # feedparser's parsed date tuple has no DST indication, we need to force it
    # because there is no UTC equivalent of mktime()
    date_tuple = date_tuple[:-1] + (-1,)
    date_tuple = time.localtime(time.mktime(date_tuple) - 3600)
    # if it is still in the future, the implementation is hopelessly broken,
    # truncate it to the present
    if date_tuple > time.gmtime():
      return time.gmtime()
    else:
      return date_tuple
  else:
    return date_tuple

# code to dereference URLs and follow redirects
class Redirect(Exception):
  def __init__(self, code, url):
    self.code = code
    self.url = url
class DontHandleRedirect(urllib2.HTTPRedirectHandler):
  """Override redirect handling to not dereference redirects for testing"""
  def http_error_302(self, req, fp, code, msg, headers):
    if 'location' in headers:
      newurl = headers.getheaders('location')[0]
    elif 'uri' in headers:
      newurl = headers.getheaders('uri')[0]
    else:
      return
    newurl = urlparse.urljoin(req.get_full_url(), newurl)
    raise Redirect(code, newurl)
  http_error_301 = http_error_303 = http_error_307 = http_error_302
redirect_opener = urllib2.build_opener(DontHandleRedirect)
socket.setdefaulttimeout(10)

def dereference(url, seen=None, level=0):
  """Recursively dereference a URL"""
  # this set is used to detect redirection loops
  if seen is None:
    seen = set([url])
  else:
    seen.add(url)
  # stop recursion if it is too deep
  if level > 16:
    return url
  try:
    url_obj = redirect_opener.open(url)
    # no redirect occurred
    return url
  except (urllib2.URLError, ValueError, socket.error):
    return url
  except Redirect, e:
    # break a redirection loop if it occurs
    if e.url in seen:
      return url
    # some servers redirect to Unicode URLs, which are not legal
    try:
      unicode(e.url)
    except UnicodeDecodeError:
      return url
    # there might be several levels of redirection
    return dereference(e.url, seen, level + 1)
  except:
    util.print_stack()
    return url
  
url_re = re.compile('(?:href|src)="([^"]*)"', re.IGNORECASE)

def normalize(item, f, run_filters=True):
  # get rid of RDF lossage...
  for key in ['title', 'link', 'created', 'modified', 'author',
              'content', 'content_encoded', 'description']:
    if type(item.get(key)) == list:
      if len(item[key]) == 1:
        item[key] = item[key][0]
      else:
        candidate = [i for i in item[key] if i.get('type') == 'text/html']
        if len(candidate) > 1 and key == 'content':
          candidate = sorted(candidate,
                             key=lambda i: len(i.get('value', '')),
                             reverse=True)[:1]
        if len(candidate) == 1:
          item[key] = candidate[0]
        else:
          # XXX not really sure how to handle these cases
          print >> param.log, 'E' * 16, 'ambiguous RDF', key, item[key]
          item[key] = item[key][0]
    if isinstance(item.get(key), dict) and 'value' in item[key]:
      item[key] = item[key]['value']
  ########################################################################
  # title
  if 'title' not in item or not item['title'].strip():
    item['title'] = 'Untitled'
  # XXX for debugging
  if type(item['title']) not in [str, unicode]:
    print >> param.log, 'TITLE' * 15
    import code
    from sys import exit
    code.interact(local=locals())
  item['title_lc'] =   lower(item['title'])
  item['title_words_exact'] =  get_words(item['title_lc'])
  item['title_words'] =  stem(item['title_words_exact'])
  ########################################################################
  # link
  #
  # The RSS 2.0 specification allows items not to have a link if the entry
  # is complete in itself
  # that said this is almost always spurious, so we filter it below
  if 'link' not in item:
    item['link'] = f['channel']['link']
    # We have to be careful not to assign a default URL as the GUID
    # otherwise only one item will ever be recorded
    if 'id' not in item:
      item['id'] = 'HASH_CONTENT'
      item['RUNT'] = True
  if type(item['link']) == unicode:
    item['link'] = str(item['link'].encode('UTF-8'))
  if type(item['link']) != str:
    print >> param.log, 'LINK IS NOT str', repr(item['link'])
  # XXX special case handling for annoying Sun/Roller malformed entries
  if 'blog.sun.com' in item['link'] or 'blog.sun.com' in item['link']:
    item['link'] = item['link'].replace(
      'blog.sun.com', 'blogs.sun.com').replace(
      'blogs.sun.com/page', 'blogs.sun.com/roller/page')
  ########################################################################
  # GUID
  if 'id' not in item:
    item['id'] = item['link']
  ########################################################################
  # creator
  if 'author' not in item or item['author'] == 'Unknown':
    item['author'] = 'Unknown'
    if 'author' in f['channel']:
      item['author'] = f['channel']['author']
  ########################################################################
  # created amd modified dates
  if 'modified' not in item:
    item['modified'] = f['channel'].get('modified')
  # created - use modified if not available
  if 'created' not in item:
    if 'modified_parsed' in item:
      created = item['modified_parsed']
    else:
      created = None
  else:
    created = item['created_parsed']
  if not created:
    # XXX use HTTP last-modified date here
    created = time.gmtime()
    # feeds that do not have timestamps cannot be garbage-collected
    # XXX need to find a better heuristic, as high-volume sites such as
    # XXX The Guardian, CNET.com or Salon.com lack item-level timestamps
    f['oldest'] = '1970-01-01 00:00:00'
  created = fix_date(created)
  item['created'] = time.strftime(date_fmt, created)
  # keep track of the oldest item still in the feed file
  if 'oldest' not in f:
    f['oldest'] = '9999-99-99 99:99:99'
  if item['created'] < f['oldest']:
    f['oldest'] = item['created']
  # finish modified date
  if 'modified_parsed' in item and item['modified_parsed']:
    modified = fix_date(item['modified_parsed'])
    # add a fudge factor time window within which modifications are not
    # counted as such, 10 minutes here
    if not modified or abs(time.mktime(modified) - time.mktime(created)) < 600:
      item['modified'] = None
    else:
      item['modified'] = time.strftime(date_fmt, modified)
  else:
    item['modified'] = None
  ########################################################################
  # content
  if 'content' in item:
    content = item['content']
  elif 'content_encoded' in item:
    content = item['content_encoded']
  elif 'description' in item:
    content = item['description']
  else:
    content = '<a href="' + item['link'] + '">' + item['title'] + '</a>'
  if not content:
    content = '<a href="' + item['link'] + '">' + item['title'] + '</a>'
  # strip embedded NULs as a defensive measure
  content = content.replace('\0', '')
  # apply ad filters and other degunking to content
  old_content = None
  while old_content != content:
    old_content = content
    try:
      for filter in transform.filter_list:
        content = filter.apply(content, f, item)
    except:
      util.print_stack(black_list=['item'])
  # balance tags like <b>...</b>
  content = balance(content)
  content_lc = lower(content)
  # the content might have invalid 8-bit characters.
  # Heuristic suggested by Georg Bauer
  if type(content) != unicode:
    try:
      content = content.decode('utf-8')
    except UnicodeError:
      content = content.decode('iso-8859-1')
  #
  item['content'] = content
  # we recalculate this as content may have changed due to tag rebalancing, etc
  item['content_lc'] = lower(content)
  item['content_words_exact'] = get_words(item['content_lc'])
  item['content_words'] = stem(item['content_words_exact'])
  item['union_lc'] = item['title_lc'] + '\n' + item['content_lc']
  item['union_words'] = item['title_words'].union(item['content_words'])
  item['urls'] = url_re.findall(content)
  ########################################################################
  # categories/tags
  # we used 'category' before, but 'category' and 'categories' are
  # intercepted by feedparser.FeedParserDict.__getitemm__ and treated as
  # special case
  if 'tags' in item and type(item['tags']) == list:
    item['item_tags'] = set([lower(t['term']) for t in item['tags']])
  else:
    item['item_tags'] = []
  ########################################################################
  # map unicode
  for key in ['title', 'link', 'created', 'modified', 'author', 'content']:
    if type(item.get(key)) == unicode:
      item[key] = item[key].encode('ascii', 'xmlcharrefreplace')
  # hash the content as the GUID if required
  if item['id'] == 'HASH_CONTENT':
    item['id']= hashlib.md5(item['title'] + item['content']).hexdigest()
  
def escape_xml(s):
  """Escape entities for a XML target"""
  return s.decode('latin1').replace('&', '&amp;').encode('ascii', 'xmlcharrefreplace').replace("'", "&apos;").replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

def escape_html(s):
  """Escape entities for a HTML target.
Differs from XML in that &apos; is defined by W3C but not implemented widely"""
  return s.decode('latin1').replace('&', '&amp;').encode('ascii', 'xmlcharrefreplace').replace("'", "&#39;").replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
