#!/usr/bin/python

import logging, logging.handlers
import argparse
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

log = logging.getLogger(__name__)

ASCII=" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

HEADER = """
#ifndef %s
#define %s

static const byte %s[] = {
// width px, height px, startchar, numchars,
%d, %d, %d, %d
// font data
"""

FOOTER = """
};
#endif // %s
"""

class CreateBMP(object):
  def __init__(self, opts):
    self.font = ImageFont.truetype(opts.font, opts.points)

    width, _, height = opts.size.partition(',')
    self.width = int(width)
    self.height = int(height)
    self.text = ASCII[opts.startchar-32:opts.endchar-31]

    chars = opts.endchar - opts.startchar
    self.imagewidth = (self.width + 1) * chars
    self.imageheight = self.height + 2

    self.image = Image.new("RGB", (self.imagewidth, self.imageheight), (255,255,255))
    draw = ImageDraw.Draw(image)

    f=ImageFont.truetype("PixelLCD-7.ttf",54)
    draw.text((0,5), "0123456789.,-+",(0,0,0), font=f)
    image.save('lcd.bmp')

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
  parser.add_argument('-f', '--font', default=None, required=True, help='Font file to read')
  parser.add_argument('-s', '--size', default=None, required=True, help='Font size (w,h)')
  parser.add_argument('-p', '--points', default=None, required=True, help='Font point size (24)')
  parser.add_argument('-c', '--startchar', default='0x20', help='Starting char in hex (0x20 space)')
  parser.add_argument('-e', '--endchar', default='0x7f', help='Ending char (0x7f del)')
  parser.add_argument('-o', '--outfile', default='font.h', help='Output header file (font.h)')
  parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output (false)')

  args = parser.parse_args()
  setup_logger(args.debug)
  opts.startchar = int(args.startchar, 16)
  opts.endchar = int(args.endchar, 16)
  if args.startchar < 32 or args.startchar > 127 or
     args.endchar < 32 or args.endchar > 127 or
     args.startchar > args.endchar:
    log.error('Invalid character definitions, must be between 0x20 (32) and 0x7f (127)')

  processor = CreateBMP(args)
  processor.process()
  log.info('Done!')

