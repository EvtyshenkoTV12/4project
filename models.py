from app import db

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    students = db.relationship('Student', backref='room', lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.Integer, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'course': self.course,
            'specialty': self.specialty,
            'gender': self.gender,
            'room_id': self.room_id
        }
