# -*- coding: utf-8 -*-

from peewee import *
from app import db


class CustomContainerField(Field):
    db_field = 'custom_container'

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        return eval(value)


class LogicLabelsField(CustomContainerField):
    db_field = 'labels'


class MissingIndicesField(CustomContainerField):
    db_field = 'missing_indices'


class StructureField(CustomContainerField):
    db_field = 'structure'


class TruthTableField(CustomContainerField):
    db_field = 'truth_table'


SqliteDatabase.register_fields({
    'labels': 'labels',
    'missing_indices': 'missing_indices',
    'structure': 'structure',
    'truth_table': 'truth_table'
})


class BaseModel(Model):
    class Meta:
        database = db


class CircuitInfo(BaseModel):
    name = CharField(default="")
    input_size = IntegerField(default=0)
    output_size = IntegerField(default=0)
    normal_size = IntegerField(default=0)
    labels = LogicLabelsField(default=[])


class SimResult(BaseModel):
    circuit = ForeignKeyField(CircuitInfo, related_name="sim_results")
    dir_idx = IntegerField(default=0)
    file_idx = IntegerField(default=0)
    structure = StructureField(default=[])
    missing_indices = MissingIndicesField(default=[])
    qca_file_path = CharField(default="")
    sim_file_path = CharField(default="")
    truth_table = TruthTableField(default=[])
    logic_expr = CharField(default="")


class Statistics(BaseModel):
    circuit = ForeignKeyField(CircuitInfo, related_name="statistics")
    dir_idx = IntegerField(default=0)
    total_count = IntegerField(default=0)
    correct_size = IntegerField(default=0)
    incorrect_size = IntegerField(default=0)
    error_rate = FloatField(default=0.0)


if __name__ == "__main__":
    db.connect()
    db.create_tables([CircuitInfo, SimResult])

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

    for sim in SimResult.select():
        print(sim.structure)
        print(sim.truth_table)
