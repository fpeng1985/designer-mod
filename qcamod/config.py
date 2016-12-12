# -*- coding: utf-8 -*-

import os
from peewee import SqliteDatabase


outdir = os.path.join(os.getcwd(), "output")

sqlite3_db = SqliteDatabase(":memory:")