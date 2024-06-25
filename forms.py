from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired

class RoomForm(FlaskForm):
    room_number = IntegerField('Номер кімнати', validators=[DataRequired()])
    room_type = StringField('Тип кімнати', validators=[DataRequired()])
    floor = IntegerField('Поверх', validators=[DataRequired()])
    capacity = IntegerField('Місткість', validators=[DataRequired()])
    gender = SelectField('Гендер кімнати', choices=[('male', 'Чоловіча'), ('female', 'Жіноча')], validators=[DataRequired()])
    submit = SubmitField('Додати')

class StudentForm(FlaskForm):
    first_name = StringField('Ім\'я', validators=[DataRequired()])
    last_name = StringField('Прізвище', validators=[DataRequired()])
    course = IntegerField('Курс', validators=[DataRequired()])
    specialty = StringField('Спеціальність', validators=[DataRequired()])
    room_number = IntegerField('Номер кімнати', validators=[DataRequired()])
    gender = SelectField('Гендер студента', choices=[('male', 'Чоловічий'), ('female', 'Жіночий')], validators=[DataRequired()])
    submit = SubmitField('Додати')