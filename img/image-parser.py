#!/usr/bin/python

import logging, logging.handlers
import argparse
from PIL import Image

BLACK = (0,0,0)

HEADER = """
#ifndef %s
#define %s

static const byte %s[] = {
"""

FOOTER = """
};
#endif // %s
"""
log = logging.getLogger(__name__)

class BmpImport(object):
  def __init__(self, opts):
    self.imgfn = opts.imgfile
    self.outfn = opts.outfile.upper().replace('.', '_')
    self.outfile = open(opts.outfile, 'w')

    self.image = Image.open(self.imgfn)
    self.width, self.height = self.image.size
    if self.height % 8 != 0:
      raise NotImplementedError('Images must have a height with a factor of 8pixels')

    log.debug('%s width:%d height:%d', opts.outfile, self.width, self.height)

  def process(self):
    rows = self.height / 8
    outcols = 16 if self.width > 16 else self.width
    rc = 0
    c = 0
    size = self.width * self.height

    self.writeheader()
    self.outfile.write('\n  ')
    for row in range(0, rows):

      for col in range(0, self.width):

        byte = 0x00
        for bit in range(0, 8):
          pixel = self.image.getpixel((col, row*8+bit))
          if pixel == BLACK:
            byte |= (2**bit)
          c += 1

        h = hex(byte)
        if len(h) == 3:
          # prepend a 0 if single digit value, 0x7 -> 0x07
          h = '0x0' + h[2]
        self.outfile.write(h)

        if c < size-1:
          self.outfile.write(', ')

        rc += 1
        if rc == outcols:
          rc = 0
          self.outfile.write('\n  ')

    self.writefooter()

  def writeheader(self):
    header = HEADER % (self.outfn, self.outfn, self.outfn[0:len(self.outfn)-2])
    self.outfile.write(header)

  def writefooter(self):
    self.outfile.write(FOOTER % self.outfn)

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
  parser.add_argument('-o', '--outfile', default='image.h', help='Output header file (image.h)')
  parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output (false)')

  args = parser.parse_args()
  setup_logger(args.debug)

  processor = BmpImport(args)
  processor.process()
  log.info('Done!')

