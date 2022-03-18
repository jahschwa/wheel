#!/usr/bin/env python3
#
# As = 2*2 = 4
# Ac = pi*(1^2) = pi
#
# Ac/As = pi/4

import random

def main():

  r = random.SystemRandom()
  steps = 0
  circle = 0
  square = 0
  while True:
    for i in range(1000000):
      x = r.random()*2-1
      y = r.random()*2-1
      if x**2+y**2<=1:
        circle += 1
      else:
        square += 1
    steps += 1000000
    print('%10s %s' % (steps,4.0*circle/(circle+square)))

if __name__=='__main__':
  main()

