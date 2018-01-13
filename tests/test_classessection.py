#!/usr/bin/env python
#coding:utf-8
# Author:  mozman -- <mozman@gmx.at>
# Purpose: test entity section
# Created: 15.03.2011
# Copyright (C) 2011, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals

import unittest
from io import StringIO

from ezdxf.tools.test import DrawingProxy, Tags, compile_tags_without_handles
from ezdxf.sections.classes import ClassesSection
from ezdxf.lldxf.tagwriter import TagWriter

class TestClassesSection(unittest.TestCase):
    def setUp(self):
        self.dwg = DrawingProxy('AC1009')
        self.section = ClassesSection(Tags.from_text(TESTCLASSES), self.dwg)

    def test_write(self):
        stream = StringIO()
        self.section.write(TagWriter(stream))
        result = stream.getvalue()
        stream.close()
        t1 = list(compile_tags_without_handles(TESTCLASSES))
        t2 = list(compile_tags_without_handles(result))
        self.assertEqual(t1, t2)

    def test_empty_section(self):
        tags = list(Tags.from_text(EMPTYSEC))
        section = ClassesSection(tags, self.dwg)
        stream = StringIO()
        section.write(TagWriter(stream))
        result = stream.getvalue()
        stream.close()
        self.assertEqual(EMPTYSEC, result)


EMPTYSEC = """  0
SECTION
  2
CLASSES
  0
ENDSEC
"""

TESTCLASSES = """  0
SECTION
  2
CLASSES
  0
CLASS
  1
ACDBDICTIONARYWDFLT
  2
AcDbDictionaryWithDefault
  3
ObjectDBX Classes
 90
        0
 91
        1
280
     0
281
     0
  0
CLASS
  1
DICTIONARYVAR
  2
AcDbDictionaryVar
  3
ObjectDBX Classes
 90
        0
 91
       13
280
     0
281
     0
  0
CLASS
  1
TABLESTYLE
  2
AcDbTableStyle
  3
ObjectDBX Classes
 90
     4095
 91
        1
280
     0
281
     0
  0
ENDSEC
"""

if __name__ == '__main__':
    unittest.main()