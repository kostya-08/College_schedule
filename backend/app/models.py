from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    course = Column(Integer)
    students_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="group", cascade="all, delete-orphan")
    subjects = relationship("GroupSubject", back_populates="group", cascade="all, delete-orphan")


class Teacher(Base):
    __tablename__ = 'teachers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String)
    max_hours_per_week = Column(Integer, default=24)
    unavailable_hours = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="teacher", cascade="all, delete-orphan")
    subjects = relationship("TeacherSubject", back_populates="teacher", cascade="all, delete-orphan")


class TeacherSubject(Base):
    __tablename__ = 'teacher_subjects'
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'))
    
    teacher = relationship("Teacher", back_populates="subjects")
    subject = relationship("Subject", back_populates="teachers")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class GroupSubject(Base):
    __tablename__ = 'group_subjects'
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'))
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'))
    
    group = relationship("Group", back_populates="subjects")
    subject = relationship("Subject", back_populates="groups")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Subject(Base):
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    total_hours = Column(Integer)
    hours_per_week = Column(Integer)
    subject_type = Column(String, default='common')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="subject", cascade="all, delete-orphan")
    teachers = relationship("TeacherSubject", back_populates="subject", cascade="all, delete-orphan")
    groups = relationship("GroupSubject", back_populates="subject", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'))
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    day_of_week = Column(Integer)
    start_time = Column(String)
    end_time = Column(String)
    room = Column(String)
    week_type = Column(String, default="all")
    semester = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("Group", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")
    subject = relationship("Subject", back_populates="schedules")
    
    def to_dict(self):
        day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        return {
            'id': self.id,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'subject_type': self.subject.subject_type if self.subject else None,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'day_of_week': self.day_of_week,
            'day_name': day_names[self.day_of_week] if self.day_of_week is not None and self.day_of_week < len(day_names) else '',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'room': self.room,
            'week_type': self.week_type,
            'semester': self.semester
        }


class Semester(Base):
    __tablename__ = 'semesters'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    semester_number = Column(Integer)
    year = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'semester_number': self.semester_number,
            'year': self.year,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None
        }