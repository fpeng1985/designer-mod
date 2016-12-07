# -*- coding: utf-8 -*-

from peewee import SqliteDatabase
from playhouse.sqliteq import SqliteQueueDatabase

outdir = r'C:\Users\fpeng\Documents\sim_manager'

db = SqliteQueueDatabase(r'C:\Users\fpeng\Documents\sim_manager\qca.db')
