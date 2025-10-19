from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    IntegerField,
    SubmitField,
    StringField,
    TextAreaField,
    HiddenField,
    PasswordField,
)
from wtforms.validators import NumberRange, DataRequired, EqualTo, ValidationError

from auth_helpers import current_user
from database import db_session
from models import Action


class ActivitySummaryForm(FlaskForm):
    action_id = SelectField("Activity", coerce=int, validators=[DataRequired()])
    days = IntegerField("Days", default=30, validators=[NumberRange(min=1, max=365)])
    submit = SubmitField("Update")


class EditActionForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)")
    submit = SubmitField("Save Changes")


class TimeframeForm(FlaskForm):
    days = IntegerField(
        "Number of days",
        validators=[DataRequired(), NumberRange(min=3, max=365)],
        default=30,
    )
    submit = SubmitField("Update", render_kw={"class": "btn btn-primary"})


class EditActivityForm(FlaskForm):
    delta = IntegerField(
        "Delta (amount)",
        default=1,
        validators=[DataRequired(), NumberRange(min=-1000, max=1000)],
    )
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)")
    submit = SubmitField("Save Changes")


class LogActivityForm(FlaskForm):
    delta = IntegerField(
        "Delta (amount)",
        default=1,
        validators=[DataRequired(), NumberRange(min=-1000, max=1000)],
    )
    notes = TextAreaField("Notes")
    properties = TextAreaField("Properties (JSON)", default="{}")
    submit = SubmitField("Save Changes")


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={"autocomplete": "username", "class": "auth-input"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password", "class": "auth-input"},
    )
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={"autocomplete": "username", "class": "auth-input"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "new-password", "class": "auth-input"},
    )
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


class NewActionForm(FlaskForm):
    name = StringField(
        "Name", validators=[DataRequired()], render_kw={"autocomplete": "activity"}
    )
    notes = TextAreaField("Notes", default="")
    properties = TextAreaField("Properties (JSON)", default="{}")
    submit = SubmitField("Save Changes")

    def validate_name(self, field):
        user = current_user()
        if not user:
            raise ValidationError("Authentication required.")

        # Check if the user already has an action with this name
        existing = (
            db_session.query(Action).filter_by(user_id=user.id, name=field.data).first()
        )
        if existing:
            raise ValidationError("Duplicate action name.")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Change Password")
    action = HiddenField(default="change_password")


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Delete My Account")
    action = HiddenField(default="delete_account")
