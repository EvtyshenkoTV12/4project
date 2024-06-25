from flask import Flask, render_template, redirect, url_for, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine
import pandas as pd
import os
from matplotlib import pyplot as plt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dormitory.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import Room, Student
from forms import StudentForm, RoomForm

# Збір даних із бази даних
def get_data_as_dataframe():
    # Отримання даних про кімнати та студентів
    rooms = Room.query.all()
    students = Student.query.all()
    
    # Створення DataFrame для кімнат
    rooms_data = [{
        'room_id': room.id,
        'room_number': room.room_number,
        'room_type': room.room_type,
        'floor': room.floor,
        'capacity': room.capacity,
        'gender': room.gender,
        'current_occupancy': len(room.students)
    } for room in rooms]
    
    rooms_df = pd.DataFrame(rooms_data)

    # Створення DataFrame для студентів
    students_data = [student.to_dict() for student in students]
    students_df = pd.DataFrame(students_data)

    return rooms_df, students_df

# Візуалізація даних
def plot_student_gender_distribution(students_df):
    # Розподіл студентів за гендером
    gender_counts = students_df['gender'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=140, colors=['lightblue', 'lightpink'])
    plt.title('Розподіл студентів за гендером')
    plt.savefig('static/charts/student_gender_distribution.png')
    plt.close()

def plot_room_occupancy(rooms_df):
    # Заповненість кімнат
    total_capacity = rooms_df['capacity'].sum()
    total_occupied = rooms_df['current_occupancy'].sum()
    free_spots = total_capacity - total_occupied
    
    plt.figure(figsize=(8, 8))
    plt.pie([total_occupied, free_spots], labels=['Зайнято', 'Вільно'], autopct='%1.1f%%', startangle=140, colors=['lightgreen', 'lightgrey'])
    plt.title('Заповненість кімнат (%)')
    plt.savefig('static/charts/room_occupancy_rate.png')
    plt.close()

def plot_course_distribution(students_df):
    # Розподіл студентів за курсами
    plt.figure(figsize=(10, 6))
    course_counts = students_df['course'].value_counts()
    plt.bar(course_counts.index, course_counts.values, color='green')
    plt.xlabel('Курс')
    plt.ylabel('Кількість студентів')
    plt.title('Розподіл студентів за курсами')
    plt.savefig('static/charts/course_distribution.png')
    plt.close()

def plot_specialty_distribution(students_df):
    # Розподіл студентів за спеціальностями
    plt.figure(figsize=(10, 6))
    specialty_counts = students_df['specialty'].value_counts()
    plt.bar(specialty_counts.index, specialty_counts.values, color='orange')
    plt.xticks(rotation=45, ha="right")
    plt.xlabel('Спеціальність')
    plt.ylabel('Кількість студентів')
    plt.title('Розподіл студентів за спеціальностями')
    plt.savefig('static/charts/specialty_distribution.png')
    plt.close()

def plot_gender_distribution(rooms_df):
    # Розподіл кімнат за гендером
    plt.figure(figsize=(10, 6))
    gender_counts = rooms_df['gender'].value_counts()
    plt.bar(gender_counts.index, gender_counts.values, color='purple')
    plt.xlabel('Гендер')
    plt.ylabel('Кількість кімнат')
    plt.title('Розподіл кімнат за гендером')
    plt.savefig('static/charts/gender_distribution.png')
    plt.close()

@app.route('/')
def index():
    search_filter = request.args.get('search_filter', '')
    floor_filter = request.args.get('floor_filter')
    free_first = request.args.get('free_first') == 'on'
    full_first = request.args.get('full_first') == 'on'
    hide_full = request.args.get('hide_full') == 'on'
    hide_empty = request.args.get('hide_empty') == 'on'

    query = Room.query

    if search_filter.isdigit():
        query = query.filter_by(room_number=int(search_filter))
    elif search_filter:
        student_rooms = Student.query.filter(
            db.or_(
                Student.first_name.ilike(f"%{search_filter}%"),
                Student.last_name.ilike(f"%{search_filter}%")
            )
        ).all()
        room_ids = {student.room_id for student in student_rooms}
        query = Room.query.filter(Room.id.in_(room_ids))
    else:
        query = query.order_by(Room.room_number)

    if floor_filter and floor_filter.isdigit():
        query = query.filter_by(floor=int(floor_filter))

    rooms = query.all()

    if free_first and not full_first:
        rooms.sort(key=lambda r: r.capacity - len(r.students), reverse=True)
    elif full_first and not free_first:
        rooms.sort(key=lambda r: r.capacity - len(r.students))

    if hide_full:
        rooms = [r for r in rooms if len(r.students) < r.capacity]
    if hide_empty:
        rooms = [r for r in rooms if len(r.students) > 0]

    return render_template('index.html', rooms=rooms, form_student=StudentForm(), form_room=RoomForm())

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    form = StudentForm()
    error_message = None

    if form.validate_on_submit():
        room = Room.query.filter_by(room_number=form.room_number.data).first()
        if not room:
            error_message = 'Кімнати з таким номером не існує. Перевірте введені дані.'
            return render_template('add_student.html', form=form, error_message=error_message)

        if room.gender != form.gender.data:
            error_message = 'Гендер студента не відповідає гендеру кімнати.'
            return render_template('add_student.html', form=form, error_message=error_message)

        if len(room.students) >= room.capacity:
            error_message = 'Кімната заповнена. Не можна додати більше студентів.'
            return render_template('add_student.html', form=form, error_message=error_message)

        student = Student(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            course=form.course.data,
            specialty=form.specialty.data,
            gender=form.gender.data,
            room_id=room.id
        )
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add_student.html', form=form, error_message=error_message)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    form = RoomForm()
    error_message = None

    if form.validate_on_submit():
        existing_room = Room.query.filter_by(room_number=form.room_number.data).first()
        if existing_room:
            error_message = 'Кімната з таким номером вже існує.'
            return render_template('add_room.html', form=form, error_message=error_message)

        room = Room(
            room_number=form.room_number.data,
            room_type=form.room_type.data,
            floor=form.floor.data,
            capacity=form.capacity.data,
            gender=form.gender.data
        )
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add_room.html', form=form, error_message=error_message)

@app.route('/update_room/<int:room_id>', methods=['POST'])
def update_room(room_id):
    data = request.json
    print("Отримані дані для оновлення:", data)

    room = Room.query.get(room_id)
    if not room:
        print(f"Помилка: кімната з ID {room_id} не знайдена")
        return jsonify({'error': 'Кімната не знайдена'}), 404

    current_student_count = len(room.students)
    new_capacity = int(data.get('capacity'))
    print(f"Кількість студентів у кімнаті: {current_student_count}")
    print(f"Нова місткість: {new_capacity}")

    if current_student_count > new_capacity:
        print(f"Помилка: місткість не може бути менша за кількість студентів у кімнаті (студентів: {current_student_count}, нова місткість: {new_capacity})")
        return jsonify({'error': 'Місткість не може бути менша за кількість студентів у кімнаті.'}), 400

    # Оновлення даних кімнати
    room.room_type = data.get('roomType')
    room.floor = int(data.get('floor'))
    room.capacity = new_capacity
    room.gender = data.get('gender')

    try:
        db.session.commit()
        print(f"Дані кімнати {room_id} оновлено")
        return jsonify({'message': 'Дані кімнати оновлено'}), 200
    except Exception as e:
        print(f"Помилка під час збереження змін: {e}")
        db.session.rollback()
        return jsonify({'error': 'Не вдалося оновити дані кімнати.'}), 500

@app.route('/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    data = request.json
    print("Отримані дані для оновлення студента:", data)

    student = Student.query.get(student_id)
    if not student:
        print(f"Помилка: студент з ID {student_id} не знайдений")
        return jsonify({'error': 'Студент не знайдений'}), 404

    room = Room.query.filter_by(room_number=data.get('roomNumber')).first()
    if not room:
        print(f"Помилка: кімната з номером {data.get('roomNumber')} не знайдена")
        return jsonify({'error': 'Кімната не знайдена'}), 404

    if room.gender != data.get('gender'):
        print(f"Помилка: гендер студента ({data.get('gender')}) не відповідає гендеру кімнати ({room.gender})")
        return jsonify({'error': 'Гендер не відповідає'}), 400

    current_student_count = len(room.students)
    new_capacity = room.capacity
    print(f"Кількість студентів у кімнаті: {current_student_count}")
    print(f"Нова місткість: {new_capacity}")

    if current_student_count >= new_capacity and room.id != student.room_id:
        print(f"Помилка: місткість кімнати перевищена (студентів: {current_student_count}, місткість: {new_capacity})")
        return jsonify({'error': 'Місткість кімнати перевищена.'}), 400

    # Оновлення даних студента
    student.course = data.get('course')
    student.specialty = data.get('specialty')
    student.room_id = room.id

    try:
        db.session.commit()
        print(f"Дані студента {student_id} оновлено")
        return jsonify({'message': 'Дані студента оновлено'}), 200
    except Exception as e:
        print(f"Помилка під час збереження змін: {e}")
        db.session.rollback
        return jsonify({'error': 'Не вдалося оновити дані студента.'}), 500

@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    print(f"Спроба видалення кімнати з ID: {room_id}")
    room = Room.query.get(room_id)
    if not room:
        print(f"Помилка: кімната з ID {room_id} не знайдена")
        return jsonify({'error': 'Кімната не знайдена'}), 404

    if len(room.students) > 0:
        print(f"Помилка: в кімнаті {room_id} є студенти")
        return jsonify({'error': 'Видалення неможливе: в кімнаті є студенти'}), 400

    db.session.delete(room)
    db.session.commit()
    print(f"Кімната {room_id} видалена")
    return jsonify({'message': 'Кімната видалена'}), 200

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    print(f"Спроба видалення студента з ID: {student_id}")
    student = Student.query.get(student_id)
    if not student:
        print(f"Помилка: студент з ID {student_id} не знайдений")
        return jsonify({'error': 'Студент не знайдений'}), 404

    db.session.delete(student)
    db.session.commit()
    print(f"Студент {student_id} видалений")
    return jsonify({'message': 'Студент видалений'}), 200

@app.route('/room_students/<int:room_id>', methods=['GET'])
def room_students(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'error': 'Кімната не знайдена'}), 404

    students = [{'id': student.id, 'first_name': student.first_name, 'last_name': student.last_name, 'course': student.course, 'specialty': student.specialty, 'gender': student.gender} for student in room.students]
    return jsonify({'students': students}), 200

@app.route('/analytics')
def analytics():
    rooms_df, students_df = get_data_as_dataframe()

    # Створення графіків
    plot_course_distribution(students_df)
    plot_specialty_distribution(students_df)
    plot_gender_distribution(rooms_df)
    plot_student_gender_distribution(students_df)
    plot_room_occupancy(rooms_df)
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(debug=True)
