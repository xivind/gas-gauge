from peewee import Model, CharField, IntegerField, ForeignKeyField, TextField, DateTimeField
from database import db
from datetime import datetime

class BaseModel(Model):
    class Meta:
        database = db

class CanisterType(BaseModel):
    name = CharField(unique=True)
    full_weight = IntegerField()  # grams
    empty_weight = IntegerField()  # grams

    @property
    def gas_capacity(self):
        return self.full_weight - self.empty_weight

class Canister(BaseModel):
    id = CharField(primary_key=True)  # UUID-based string
    label = CharField(max_length=64)  # User-editable friendly name
    canister_type = ForeignKeyField(CanisterType, backref='canisters')
    status = CharField(default='active')  # active or depleted
    created_at = DateTimeField(default=datetime.now)

class Weighing(BaseModel):
    canister = ForeignKeyField(Canister, backref='weighings')
    weight = IntegerField()  # grams
    comment = TextField(null=True)
    recorded_at = DateTimeField(default=datetime.now)

    @property
    def remaining_gas(self):
        return self.weight - self.canister.canister_type.empty_weight

    @property
    def remaining_percentage(self):
        capacity = self.canister.canister_type.gas_capacity
        if capacity == 0:
            return 0
        return (self.remaining_gas / capacity) * 100

    @property
    def consumption_percentage(self):
        return 100 - self.remaining_percentage
