# -*- coding: utf-8 -*-

import os
from peewee import SqliteDatabase

outdir = os.path.join(os.getcwd(), "output")

db = SqliteDatabase(os.path.join(outdir, "qca.db"))

