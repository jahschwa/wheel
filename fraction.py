#!/usr/bin/env python3
#
# https://docs.python.org/3/reference/datamodel.html#special-method-names

from functools import total_ordering, wraps

def with_fractions(*dec_args, **dec_kwargs):
  """Parse args into Fraction objects."""

  def outer(func):
    @wraps(func)
    def decorate(*args, **kwargs):
      try:
        args = [Fraction.parse(x) for x in args]
        kwargs = {k:Fraction.parse(v) for (k,v) in kwargs.items()}
      except TypeError:
        return NotImplemented
      if dec_kwargs.get('int_only'):
        for x in args + list(kwargs.values()):
          if x.d != 1:
            raise ValueError(
              'cannot call {} with non-int Fractions'.format(func.__name__)
            )
      return func(*args, **kwargs)
    return decorate

  # first case is @with_fractions, second is @with_fractions(int_only=True)
  if len(dec_args) == 1 and len(dec_kwargs) == 0:
    return outer(dec_args[0])
  else:
    return outer

@total_ordering
class Fraction:
  """Do math with integer fractions, avoiding floating point."""

  ##### Static methods

  @staticmethod
  def parse(x):
    if isinstance(x, Fraction):
      return x
    elif isinstance(x, int):
      return Fraction(x, 1)
    elif isinstance(x, float):
      return Fraction(*x.as_integer_ratio())
    elif isinstance(x, tuple) and 0 < len(x) < 3:
      return Fraction(*x)
    elif isinstance(x, str):
      radix = x.find('.')
      x = x.replace('.', '')
      if radix == -1:
        radix = len(x)
      return Fraction(int(x), 10**(len(x)-radix))
    else:
      raise TypeError

  @staticmethod
  def gcd(a, b):
    while b:
      (a, b) = (b, a%b)
    return a

  @staticmethod
  def lcm(a, b):
    return a*b // Fraction.gcd(a, b)

  @staticmethod
  def simplify(n, d):
    negative = False
    if n * d < 1:
      negative = True
    (n, d) = (abs(n), abs(d))
    g = Fraction.gcd(n, d)
    if negative:
      n = -n
    return (n//g, d//g)

  ##### Normal methods

  def __init__(self, n, d=1):
    if d == 0:
      raise ZeroDivisionError

    if not isinstance(n, int):
      n = Fraction.parse(n)
    if not isinstance(d, int):
      d = Fraction.parse(d)

    if any(isinstance(x, Fraction) for x in (n, d)):
      f = n / d
      (n, d) = (f.n, f.d)
    else:
      (n, d) = Fraction.simplify(n, d)

    (self.n, self.d) = (n, d)

  def __repr__(self):
    return '<Fraction {}>'.format(str(self))

  def __str__(self):
    if self.d == 1:
      return str(self.n)
    return '{}/{}'.format(self.n, self.d)

  # https://docs.python.org/3/library/string.html#format-specification-mini-language
  def __format__(self, spec):
    if any(spec.endswith(x) for x in 'bcdoxXn'):
      if self.d != 1:
        raise ValueError(
          'Unkown format code "{}" for non-int Fraction'.format(spec)
        )
      return int(self).__format__(spec)
    if any(spec.endswith(x) for x in 'eEfFgGn%'):
      return float(self).__format__(spec)
    return str(self).__format__(spec)

  def __hash__(self):
    return hash((self.n, self.d))

  def __bool__(self):
    return self.n != 0

  ##### Numeric methods - unary

  def __neg__(self):
    return Fraction(-self.n, self.d)

  def __pos__(self):
    return self

  def __abs__(self):
    return Fraction(abs(self.n), self.d)

  def __invert__(self):
    return Fraction(self.d, self.n)

  def __complex__(self):
    return complex(float(self))

  def __int__(self):
    return (self.n // self.d) + (1 if self.n < 0 else 0)

  def __float__(self):
    return self.n / self.d

  def __index__(self):
    if self.d != 1:
      raise ValueError('non-integer Fraction may not be used here')
    return self.n

  def __round__(self, digits):
    interval = Fraction(1, 10**digits)
    cutoff = interval / 2
    remainder = self % interval
    down = self - remainder
    up = down + interval

    if remainder > cutoff:
      return up
    elif remainder < cutoff:
      return down
    else:
      digit = (down % (interval * 10)) / interval
      if digit.n % 2:
        return up
      return down

  def __trunc__(self):
    return self.__floor__() if self.n > 0 else self.__ceil__()

  def __floor__(self):
    return Fraction(self.n // self.d, 1)

  def __ceil__(self):
    return self.__floor__() + (1 if self.n % self.d else 0)

  ##### Numeric methods - binary

  @with_fractions
  def __add__(self, f):
    l = Fraction.lcm(abs(self.d), abs(f.d))
    return Fraction(self.n * l // self.d + f.n * l // f.d, l)
  __radd__ = __add__

  @with_fractions
  def __sub__(self, f):
    return self + (-f)
  @with_fractions
  def __rsub__(self, f):
    return f - self

  @with_fractions
  def __mul__(self, f):
    return Fraction(self.n * f.n, self.d * f.d)
  __rmul__ = __mul__

  @with_fractions
  def __truediv__(self, f):
    return self * (~f)
  @with_fractions
  def __rtruediv__(self, f):
    return f / self

  @with_fractions
  def __floordiv__(self, f):
    return (self / f).__floor__()
  @with_fractions
  def __rfloordiv__(self, f):
    return f // self

  @with_fractions
  def __mod__(self, f):
    l = Fraction.lcm(self.d, f.d)
    return Fraction((self.n * l // self.d) % (f.n * l // f.d), l)
  @with_fractions
  def __rmod__(self, f):
    return f % self

  @with_fractions
  def __divmod__(self, f):
    return (self // f, self % f)
  @with_fractions
  def __rdivmod__(self, f):
    return divmod(f, self)

  @with_fractions
  def __pow__(self, f):
    if f < 0:
      return (~self) ** (-f)
    elif f.d == 1:
      return Fraction(self.n ** f.n, self.d ** f.n)
    else:
      return Fraction(self.n ** float(f), self.d ** float(f))
  @with_fractions
  def __rpow__(self, f):
    return f ** self

  @with_fractions(int_only=True)
  def __lshift__(self, f):
    return Fraction(self.n << f.n)
  @with_fractions(int_only=True)
  def __rlshift__(self, f):
    return f << self

  @with_fractions(int_only=True)
  def __rshift__(self, f):
    return Fraction(self.n >> f.n)
  @with_fractions(int_only=True)
  def __rrshift__(self, f):
    return f >> self

  @with_fractions(int_only=True)
  def __and__(self, f):
    return Fraction(self.n & f.n)
  __rand__ = __and__

  @with_fractions(int_only=True)
  def __xor__(self, f):
    return Fraction(self.n ^ f.n)
  __rxor__ = __xor__

  @with_fractions(int_only=True)
  def __or__(self, f):
    return Fraction(self.n | f.n)
  __ror__ = __or__

  ##### Numeric methods - comparison

  @with_fractions
  def __eq__(self, f):
    return self.n == f.n and self.d == f.d

  @with_fractions
  def __lt__(self, f):
    l = Fraction.lcm(abs(self.d), abs(f.d))
    return (self.n * l // self.d) < (f.n * l // f.d)
