# -*- coding: utf-8 -*-

import os
from peewee import SqliteDatabase

OUT_DIR = os.path.join(os.getcwd(), "output")

DB = SqliteDatabase(":memory:")

PROCESS_NUM = 20

