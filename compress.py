#!/usr/bin/env python

import sys,bisect

ESCAPE = '\\'
MAX_WORD_BITS = 4

MIN_WORD = 4
MAX_WORD = 2**MAX_WORD_BITS
MAX_REL_BITS = 16-MAX_WORD_BITS
MAX_REL = 2**MAX_REL_BITS

def compress(instr):

  s = instr.replace(ESCAPE,'')

  i = 0
  while i<len(s)-MAX_WORD:
    for l in range(MAX_WORD+MIN_WORD,MIN_WORD-1,-1):
      word = s[i:i+l]
      if '\n' in word:
        continue
      start = i+1
      while start>0:
        try:
          match = s.index(word,start)
          print '"%s" @ %s' % (word.replace('\n','\\n'),match)
        except ValueError:
          match = -1
        else:
          print (match-i,l)
          s = s[:match]+ESCAPE+encode(match-i,l)+s[match+l:]
        start = match+1
    i += 1

  return ESCAPE+s

def decompress(outstr):

  escape = outstr[0]
  s = outstr[1:]

  i = len(s)-1
  while i>=0:
    if s[i]==escape:
      (rel,length) = decode(s[i+1:i+3])
      print '%s:%s = "%s"' % (i-rel,i-rel+length,s[i-rel:i-rel+length].replace('\n','\\n'))
      s = s[:i]+s[i-rel:i-rel+length]+s[i+3:]
    i -= 1

  return s

class Document(object):

  def __init__(self,length):

    self.length = length
    self.matches = []
    self.protected = Range(length)
    self.offset = 0

  def add_match(self,match):

    for m in self.matches:
      if match.intersects(m):
        return

    r = Range(self.length,(match.found_start,match.found_end))
    if r.intersects(self.protected):
      return

    raise NotImplemented

class Match(object):

  def __init__(self,ref,length,found):

    self.ref_start = ref
    self.ref_end = ref+length-1
    self.found_start = found
    self.found_end = found+length-1

  def __lt__(self,other):

    if not isinstance(other,Match):
      raise TypeError
    return self.found_start<other.found_start

  def intersects(self,other):

    if not isinstance(other,Match):
      raise TypeError
    return (
      self.found_start<other.found_end and self.found_end>other.found_start
    )

class Range(object):

  def __init__(self,length,start=None):

    self.length = length
    if start is None:
      self.ranges = []
    elif isinstance(start,tuple):
      self.ranges = [start]
    elif isinstance(start,list):
      self.ranges = start
    else:
      raise TypeError

  def intersects(self,other):

    if not isinstance(other,Range):
      raise TypeError

    for (s1,e1) in self.ranges:
      for (s2,e2) in other.ranges:
        if s1<e2 and e1>s2:
          return True

  def copy(self):

    new = Range(self.length)
    new.ranges = [x for x in self.ranges]
    return new

  def __add__(self,other):

    if not isinstance(other,Range):
      return NotImplemented

    if self.length!=other.length:
      return ValueError

    new = self.copy()

    for (s2,e2) in other.ranges:
      right = len(new.ranges)
      inter = []
      for (i,(s1,e1)) in enumerate(new.ranges):
        if e2<s1:
          right = i
        if s1<e2 and e1>s2:
          inter.append(i)
      if inter:
        s = min(new.ranges[inter[0]][0],s2)
        e = max(new.ranges[inter[-1]][1],e2)
        del new.ranges[inter[0]:inter[-1]+1]
      else:
        (s,e) = (s2,e2)
      new.ranges.insert(right,(s,e))

    return new

  def __str__(self):

    result = ['-']*self.length
    for (s,e) in self.ranges:
      result[s:e+1] = ['#']*(e-s+1)
    return ''.join(result)

def encode(rel,length):

  rel = bin(rel)[2:].zfill(MAX_REL_BITS)
  length = bin(length-MIN_WORD)[2:].zfill(MAX_WORD_BITS)
  full = rel+length
  return chr(int(full[:8],2))+chr(int(full[8:],2))

def decode(s):

  s = bin(ord(s[0]))[2:].zfill(8)+bin(ord(s[1]))[2:].zfill(8)
  rel = int(s[:MAX_REL_BITS],2)
  length = int(s[MAX_REL_BITS:],2)+MIN_WORD
  return (rel,length)

if __name__=='__main__':

  with open(sys.argv[1],'rb') as f:
    s = f.read()
  inlen = len(s)

  if sys.argv[2]=='c':
    s = compress(s)
  elif sys.argv[2]=='d':
    s = decompress(s)
  else:
    raise RuntimeError('invalid option "%s"' % s)
  with open(sys.argv[3],'wb') as f:
    f.write(s)
  outlen = len(s)

  print '(out %s) / (in %s) = %s%%\n' % (outlen,inlen,100*outlen/inlen)
