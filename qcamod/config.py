# -*- coding: utf-8 -*-

import os
from peewee import SqliteDatabase

OUT_DIR = os.path.join(os.getcwd(), "output")

DB = SqliteDatabase(":memory:", field_types={"list":"list"})

PROCESS_NUM = 20

