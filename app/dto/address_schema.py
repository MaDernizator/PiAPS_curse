from marshmallow import Schema, fields

class AddressCreateSchema(Schema):
    street = fields.String(required=True)
    building_number = fields.String(required=True)
    unit_number = fields.String(required=True)
