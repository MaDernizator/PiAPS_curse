from marshmallow import Schema, fields, validate

class InvitationCreateSchema(Schema):
    target_email = fields.Email(required=True)
    target_role = fields.Str(required=True, validate=validate.OneOf(["RESIDENT", "GUEST"]))
    address_id = fields.Int(required=True)
