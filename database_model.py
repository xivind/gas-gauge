"""
Database models for Gas Gauge application.
Simple Peewee models without magic - no ForeignKeyField, no computed properties.
"""

from peewee import Model, CharField, IntegerField, TextField, AutoField

class BaseModel(Model):
    """Base model for all database models"""
    class Meta:
        # Database is set in database_manager.py
        database = None

class CanisterType(BaseModel):
    """Model for canister types (Coleman 240g, etc.)"""
    id = AutoField()
    name = CharField(unique=True)
    full_weight = IntegerField()  # grams
    empty_weight = IntegerField()  # grams

    class Meta:
        table_name = "canistertype"

class Canister(BaseModel):
    """Model for individual canisters"""
    id = CharField(primary_key=True, unique=True)  # UUID-based string like GC-a3f8e52468
    label = CharField()  # User-editable friendly name
    canister_type_id = IntegerField()  # Plain integer, not ForeignKeyField
    status = CharField()  # active or depleted
    created_at = CharField()  # ISO format string YYYY-MM-DD HH:MM:SS

    class Meta:
        table_name = "canister"

class Weighing(BaseModel):
    """Model for weighing records"""
    id = AutoField()
    canister_id = CharField()  # Plain string, not ForeignKeyField
    weight = IntegerField()  # grams
    comment = TextField(null=True)
    recorded_at = CharField()  # ISO format string YYYY-MM-DD

    class Meta:
        table_name = "weighing"
