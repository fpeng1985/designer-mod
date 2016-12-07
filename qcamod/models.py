# -*- coding: utf-8 -*-

from peewee import *
from app import db


class ListField(Field):
    db_field = 'list'

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        return eval(value)


SqliteDatabase.register_fields({'list': 'list'})


class BaseModel(Model):
    class Meta:
        database = db


class CircuitInfo(BaseModel):
    name = CharField(unique=True)
    input_size = IntegerField(default=0)
    output_size = IntegerField(default=0)
    normal_size = IntegerField(default=0)
    labels = ListField(default=[])


class SimResult(BaseModel):
    circuit = ForeignKeyField(CircuitInfo, related_name="sim_results")
    dir_idx = IntegerField(default=0)
    file_idx = IntegerField(default=0)
    structure = ListField(default=[])
    missing_indices = ListField(default=[])
    qca_file_path = CharField(default="")
    sim_file_path = CharField(default="")
    truth_table = ListField(default=[])
    logic_expr = ListField(default=[])
    is_correct = BooleanField(default=True)


if __name__ == "__main__":
    db.connect()
    db.create_tables([CircuitInfo, SimResult], safe=True)

    structure = [
        [0,  0,  1,  0,  0],
        [0,  1,  1,  1,  0],
        [-1, 1,  1,  1, -2],
        [0,  1,  1,  1,  0],
        [0,  0,  1,  0,  0]
    ]

    circuit_info = CircuitInfo.create(name='majority_gate', input_size=3, output_size=1,
                                      labels=['I02', 'I20', 'I42', 'O24'])
    circuit_info.save()

    sim_result = SimResult.create(circuit=circuit_info, dir_idx=1, file_idx=1, structure=structure)
    sim_result.save()

    for circuit in CircuitInfo.select():
        print(circuit.name)
        print(circuit.labels)

    for sim in SimResult.select():
        print(sim.structure)
        print(sim.truth_table)
        print(sim.is_correct)
