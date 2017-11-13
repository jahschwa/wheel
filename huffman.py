#!/usr/bin/env python

import sys,time,math

VERBOSE = False
DEBUG = False

def huff(instr):

  freq = [(byte,instr.count(byte)) for byte in set(instr)]
  freq = sorted(freq,key=lambda a:a[1],reverse=True)

  if VERBOSE:
    print '\n'.join([str(x) for x in freq])+'\n'

  if len(freq)==1:
    code = {freq[0][0]:'0'}
  elif len(freq)==2:
    code = {freq[0][0]:'0',freq[1][0]:'1'}
  else:
    tree = build_tree(freq)
    if DEBUG:
      print ''
    code = decode_tree(tree)

  if DEBUG:
    print ''
  if VERBOSE:
    for (char,_) in sorted(freq,key=lambda a:a[0]):
      print '%2s = %s' % (char.replace('\n','\\n'),code[char])

  if DEBUG:
    print ''
  stream = CodeStream()
  for c in reversed(instr):
    stream.insert(code[c])
  stream.insert_code_table(code)

  return stream.to_str()

def dehuff(instr):

  tic = time.time()

  stream = DecodeStream(instr)
  decode = stream.parse_code_table()
  mapping = [(alias,char) for (alias,char) in decode.items()]
  if VERBOSE:
    for (alias,char) in sorted(mapping,key=lambda a:a[1]):
      print '%2s = %s' % (char.replace('\n','\\n'),alias)

  s = ''
  char = ''
  while True:
    char = stream.next_char(decode)
    if char:
      s += char
      if DEBUG:
        print s
    else:
      break

  return s

def build_tree(code):

  code = code[:-2]+[BinaryTree(code[-2],code[-1])]
  while len(code)>1:
    if DEBUG:
      print code
    if len(code)==2:
      code = [BinaryTree(code[0],code[1])]
      continue
    values = [(i,obj) for (i,obj) in enumerate(code)]
    values = sorted(values,key=lambda a:value(a[1]))
    left = min(values[0][0],values[1][0])
    right = max(values[0][0],values[1][0])
    tree = BinaryTree(code[left],code[right])
    code[right] = tree
    del code[left]
  return code[0]

def value(obj):

  if isinstance(obj,tuple):
    return obj[1]
  elif isinstance(obj,BinaryTree):
    return obj.total
  else:
    raise TypeError

def decode_tree(tree,code=None,prefix=None):

  code = {} if code is None else code
  prefix = prefix or ''
  if DEBUG:
    print 'code: %s | prefix: %s | left: %s | right: %s' % (len(code),prefix,tree.left,tree.right)
  if isinstance(tree.left,tuple):
    code[tree.left[0]] = prefix+'0'
  else:
    decode_tree(tree.left,code,prefix+'0')
  if isinstance(tree.right,tuple):
    code[tree.right[0]] = prefix+'1'
  else:
    decode_tree(tree.right,code,prefix+'1')
  return code

class BinaryTree(object):

  def __init__(self,left,right):

    self.left = left
    self.right = right
    self.total = value(left)+value(right)

  def __str__(self):

    return '<BT:%s>' % self.total

  __repr__ = __str__

class CodeStream(object):

  EXAMPLE = '000001[alias]100[byte][alias]100[byte]100[text]'

  def __init__(self,byte_string=None):

    self.hanging = ''
    self.string = byte_string or ''

  def insert(self,value,pad=0):

    if isinstance(value,int):
      value = bin(value)[2:]
    elif not isinstance(value,str):
      raise TypeError

    if pad and len(value)<pad:
      value = '0'*((pad-len(value)%pad)%pad)+value
    if DEBUG:
      print '%s + %s + %s' % (value,self.hanging,'|'.join([bin(ord(x))[2:].zfill(8) for x in self.string[:4]]))
    self.hanging = value+self.hanging
    while len(self.hanging)>7:
      self.string = chr(int(self.hanging[-8:],2))+self.string
      self.hanging = self.hanging[:-8]
    if DEBUG:
      print '= %s + %s' % (self.hanging,'|'.join([bin(ord(x))[2:].zfill(8) for x in self.string[:4]]))
      print '-'*40

  def insert_code_table(self,code):

    if VERBOSE:
      data = len(self.string)+(1 if self.hanging else 0)

    length = min_bits(max([len(x) for x in code.values()]))

    self.insert('0',length)

    for (char,alias) in code.items():
      self.insert(ord(char),8)
      self.insert(alias)
      self.insert(len(alias),length)

    self.string = chr(int(('1'+self.hanging).zfill(8),2))+self.string
    self.hanging = ''

    self.insert(length,8)

    if VERBOSE:
      print '\nHeader: %s bytes' % (len(self.string)-data)
      print 'Data: %s bytes' % data

  def to_str(self):

    return self.string

  def __str__(self):

    return '<CodeStream %s:%s>' % (len(self.string),len(self.hanging))

def min_bits(integer):

  return 1 if integer==0 else int(math.log(integer,2))+1

class DecodeStream(object):

  def __init__(self,byte_string):

    self.string = byte_string
    self.hanging = ''

  def next_bit(self):

    if not self.hanging:
      if not self.string:
        return None
      self.hanging = bin(ord(self.string[0]))[2:].zfill(8)
      self.string = self.string[1:]

    bit = self.hanging[0]
    self.hanging = self.hanging[1:]
    return bit

  def next_byte(self):

    if self.hanging:
      raise RuntimeError

    s = self.string[0]
    self.string = self.string[1:]
    return s

  def next_char(self,decode):

    bit = ''
    working = ''
    while True:
      bit = self.next_bit()
      if bit is None:
        return None
      working += bit
      char = decode.get(working,None)
      if char:
        return char

  def parse_code_table(self):

    length = ord(self.next_byte())

    while self.next_bit()=='0':
      pass

    decode = {}
    working = ''
    alias = ''
    alias_length = -1

    while alias_length!=0:
      working += self.next_bit()

      if alias:
        if len(working)==8:
          decode[alias] = chr(int(working,2))
          working = ''
          alias = ''

      else:
        if alias_length==-1:
          if len(working)==length:
            alias_length = int(working,2)
            working = ''
        else:
          if len(working)==alias_length:
            alias = working
            alias_length = -1
            working = ''

    return decode

if __name__=='__main__':

  tic = time.time()

  with open(sys.argv[1],'rb') as f:
    s = f.read()
  inlen = len(s)

  if sys.argv[2]=='h':
    s = huff(s)
  elif sys.argv[2]=='d':
    s = dehuff(s)
  else:
    raise RuntimeError('invalid option "%s"' % sys.argv[2])
  with open(sys.argv[3],'wb') as f:
    f.write(s)
  outlen = len(s)

  print ''
  print '%suffman took %s sec' % (['Deh','H'][sys.argv[2]=='h'],time.time()-tic)
  print '(out %s) / (in %s) = %s%%\n' % (outlen,inlen,100*outlen/inlen)
