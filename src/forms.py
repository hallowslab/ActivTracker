from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, SubmitField, StringField, TextAreaField
from wtforms.validators import NumberRange, DataRequired


class ActivitySummaryForm(FlaskForm):
    action_id = SelectField("Activity", coerce=int, validators=[DataRequired()])
    days = IntegerField("Days", default=30, validators=[NumberRange(min=1, max=365)])
    submit = SubmitField("Update")


class EditActionForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)")
    submit = SubmitField("Save Changes")


class EditActivityForm(FlaskForm):
    delta = IntegerField(
        "Delta (amount)",
        default=1,
        validators=[DataRequired(), NumberRange(min=-365, max=465)],
    )
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)")
    submit = SubmitField("Save Changes")


class LogActivityForm(FlaskForm):
    delta = IntegerField(
        "Delta (amount)",
        default=1,
        validators=[DataRequired(), NumberRange(min=-365, max=465)],
    )
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)")
    submit = SubmitField("Save Changes")


class UserAccessForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired()], render_kw={"autocomplete": "username"}
    )
    password = StringField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
