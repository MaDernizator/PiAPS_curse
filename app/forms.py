from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, Optional


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(), Length(min=2)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class AdminAddressForm(FlaskForm):
    street = StringField("Улица", validators=[DataRequired()])
    building = StringField("Дом", validators=[DataRequired()])
    unit = StringField("Квартира", validators=[DataRequired()])
    code = StringField("Уникальный код", validators=[DataRequired(), Length(max=64)])
    submit = SubmitField("Создать")


class InviteForm(FlaskForm):
    email = EmailField("Email жильца", validators=[DataRequired(), Email()])
    submit = SubmitField("Отправить приглашение")

class ProfileForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Новый пароль (необязательно)", validators=[Optional(), Length(min=6)])
    notify_invites = BooleanField("Уведомлять о приглашениях")
    notify_residents = BooleanField("Уведомлять об изменениях резидентов")
    submit = SubmitField("Сохранить изменения")