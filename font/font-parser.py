#!/usr/bin/python

import logging, logging.handlers
import argparse
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

log = logging.getLogger(__name__)

ASCII=" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
BLACK = (0,0,0)

HEADER = """
#ifndef %s
#define %s

static const byte %s[] = {
  // width px, height px, startchar, numchars,
  %d, %d, %s, %d,

  // font data: %s"""

FOOTER = """
};
#endif // %s
"""

class ParseFont(object):
  def __init__(self, opts):
    self.imgfn = opts.imgfile
    self.defname = opts.outfile.upper().replace('.', '_') # myfont.h -> MYFONT_H
    self.outfile = open(opts.outfile, 'w')

    self.font_width = opts.width
    self.font_height = opts.height
    if self.font_height % 8 != 0:
      raise NotImplementedError('Images must have a height with a factor of 8pixels')

    self.image = Image.open(self.imgfn)

    self.startchar = opts.startchar
    self.numchars = opts.endchar - opts.startchar + 1
    self.imagewidth = (self.font_width + 1) * self.numchars
    self.imageheight = self.font_height + 2
    self.chars = ASCII[opts.startchar-32:opts.endchar-31]

    log.debug('%s width:%d height:%d', opts.outfile, self.font_width, self.font_height)

  def process(self):
    rows = self.font_height / 8
    outcols = 16 if self.font_width > 16 else self.font_width
    size = self.font_width * rows * self.numchars
    cnt = 0  # output char count
    rcnt = 0 # output chars per row count

    self.writeheader()
    self.outfile.write('\n  ')
    for i in range(0, self.numchars):
      char = self.startchar + i
      hexChar = self.tohex(char)
      txtChar = self.totext(char)
      self.outfile.write('// %s | %s\n  ' % (hexChar, txtChar))
      for row in range(0, rows):
        for col in range(0, self.font_width):
          imgcol = (self.font_width * i) + col
          byte = 0x00
          for bit in range(0, 8):
            pixel = self.image.getpixel((imgcol, row*8+bit))
            pixel = pixel[0:3] # remove the alpha, if exists, only want color
            #log.debug('%d | %d -> %s', imgcol, row*8+bit, pixel)
            if pixel == BLACK:
              byte |= (2**bit)

          cnt += 1
          hb = self.tohex(byte)
          self.outfile.write(hb)
          log.debug('%d | %s %s | %d,%d | B: %d | H: %s', cnt, hexChar, txtChar, row, col, byte, hb)

          if cnt < size:
            self.outfile.write(', ')

          rcnt += 1
          if rcnt == outcols:
            rcnt = 0
            self.outfile.write('\n  ')

    self.writefooter()

  def writeheader(self):
    header = HEADER % (self.defname, self.defname, self.defname[0:len(self.defname)-2],
        self.font_width, self.font_height, self.tohex(self.startchar), self.numchars, self.chars)
    self.outfile.write(header)

  def writefooter(self):
    self.outfile.write(FOOTER % self.defname)

  def tohex(self, c):
    h = hex(c)
    if len(h) == 3:
      # prepend a 0 if single digit value, 0x7 -> 0x07
      h = '0x0' + h[2]
    return h

  def totext(self, c):
    if c == 0x20:
      return '(space)'
    if c == 0x5c:
      return '(backslash)'
    if c == 0x7f:
      return '(deg)'
    return chr(c)

def setup_logger(debug):
  logger = logging.getLogger()
  if debug:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)
  formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(formatter)
  logger.addHandler(consoleHandler)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Micro OLED Image Processor')
  parser.add_argument('-i', '--imgfile', default=None, required=True, help='Input Image file')
  parser.add_argument('-W', '--width', default=None, required=True, type=int, help='Font width')
  parser.add_argument('-H', '--height', default=None, required=True, type=int, help='Font height')
  parser.add_argument('-c', '--startchar', default='0x20', help='Starting char in hex (0x20 space)')
  parser.add_argument('-e', '--endchar', default='0x7f', help='Ending char (0x7f del)')
  parser.add_argument('-o', '--outfile', default='font.h', help='Output header file (infile.h)')
  parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output (false)')

  args = parser.parse_args()
  setup_logger(args.debug)
  args.startchar = int(args.startchar, 16)
  args.endchar = int(args.endchar, 16)
  if args.startchar < 0 or args.startchar > 127 \
     or args.endchar < 0 or args.endchar > 127 \
     or args.startchar > args.endchar:
    log.error('Invalid character definitions, must be between 0x20 (32) and 0x7f (127)')

  processor = ParseFont(args)
  processor.process()
  log.info('Done!')

