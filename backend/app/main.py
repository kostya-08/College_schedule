from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel, validator
import logging

from . import models, database
from .scheduler import AutoScheduler
from .export import ScheduleExporter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="College Schedule API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic модели
class GroupCreate(BaseModel):
    name: str
    course: int
    students_count: int

class TeacherCreate(BaseModel):
    name: str
    department: str
    max_hours_per_week: int = 24

class SubjectCreate(BaseModel):
    name: str
    total_hours: int
    hours_per_week: int
    subject_type: str = "common"
    
    @validator('subject_type')
    def validate_subject_type(cls, v):
        allowed = ['common', 'rpo_profile', 'kgid_profile']
        if v not in allowed:
            return 'common'
        return v

class TeacherSubjectCreate(BaseModel):
    teacher_id: int
    subject_id: int

class GroupSubjectCreate(BaseModel):
    group_id: int
    subject_id: int

class SchedulePeriodRequest(BaseModel):
    period_type: str  # 'week' или 'month'
    period_value: Optional[str] = None
    group_id: Optional[int] = None

# Корневые эндпоинты
@app.get("/")
def root():
    return {
        "message": "College Schedule API",
        "status": "running",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/test")
def test():
    return {"status": "ok", "message": "API is working"}

# Groups endpoints
@app.post("/api/groups")
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating group: {group}")
        
        existing = db.query(models.Group).filter(models.Group.name == group.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Группа с таким названием уже существует")
        
        db_group = models.Group(
            name=group.name,
            course=group.course,
            students_count=group.students_count
        )
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        
        logger.info(f"Group created successfully: {db_group.id}")
        return db_group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/groups")
def get_groups(db: Session = Depends(get_db)):
    try:
        return db.query(models.Group).all()
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    try:
        group = db.query(models.Group).filter(models.Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        db.delete(group)
        db.commit()
        return {"message": "Group deleted", "id": group_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Teachers endpoints
@app.post("/api/teachers")
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating teacher: {teacher}")
        
        db_teacher = models.Teacher(
            name=teacher.name,
            department=teacher.department,
            max_hours_per_week=teacher.max_hours_per_week
        )
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        
        logger.info(f"Teacher created successfully: {db_teacher.id}")
        return db_teacher
    except Exception as e:
        logger.error(f"Error creating teacher: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/teachers")
def get_teachers(db: Session = Depends(get_db)):
    try:
        return db.query(models.Teacher).all()
    except Exception as e:
        logger.error(f"Error getting teachers: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    try:
        teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        db.delete(teacher)
        db.commit()
        return {"message": "Teacher deleted", "id": teacher_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting teacher: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Subjects endpoints
@app.post("/api/subjects")
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating subject: {subject}")
        
        if not subject.name:
            raise HTTPException(status_code=400, detail="Название предмета обязательно")
        
        if subject.total_hours <= 0:
            raise HTTPException(status_code=400, detail="Общее количество часов должно быть больше 0")
        
        if subject.hours_per_week <= 0:
            raise HTTPException(status_code=400, detail="Часов в неделю должно быть больше 0")
        
        existing = db.query(models.Subject).filter(models.Subject.name == subject.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Предмет с таким названием уже существует")
        
        db_subject = models.Subject(
            name=subject.name,
            total_hours=subject.total_hours,
            hours_per_week=subject.hours_per_week,
            subject_type=subject.subject_type
        )
        db.add(db_subject)
        db.commit()
        db.refresh(db_subject)
        
        logger.info(f"Subject created successfully: {db_subject.id}")
        return db_subject
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/subjects-with-assignments")
def create_subject_with_assignments(
    subject: SubjectCreate,
    teacher_id: Optional[int] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Создать предмет и сразу назначить его преподавателю и группе
    """
    try:
        logger.info(f"Creating subject with assignments: {subject}, teacher_id={teacher_id}, group_id={group_id}")
        
        if not subject.name:
            raise HTTPException(status_code=400, detail="Название предмета обязательно")
        
        if subject.total_hours <= 0:
            raise HTTPException(status_code=400, detail="Общее количество часов должно быть больше 0")
        
        if subject.hours_per_week <= 0:
            raise HTTPException(status_code=400, detail="Часов в неделю должно быть больше 0")
        
        existing = db.query(models.Subject).filter(models.Subject.name == subject.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Предмет с таким названием уже существует")
        
        # Создаем предмет
        db_subject = models.Subject(
            name=subject.name,
            total_hours=subject.total_hours,
            hours_per_week=subject.hours_per_week,
            subject_type=subject.subject_type
        )
        db.add(db_subject)
        db.flush()
        
        # Если указан преподаватель, назначаем ему предмет
        if teacher_id:
            teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
            if teacher:
                existing = db.query(models.TeacherSubject).filter(
                    models.TeacherSubject.teacher_id == teacher_id,
                    models.TeacherSubject.subject_id == db_subject.id
                ).first()
                
                if not existing:
                    teacher_subject = models.TeacherSubject(
                        teacher_id=teacher_id,
                        subject_id=db_subject.id
                    )
                    db.add(teacher_subject)
                    logger.info(f"Subject assigned to teacher {teacher_id}")
        
        # Если указана группа, назначаем предмет группе
        if group_id:
            group = db.query(models.Group).filter(models.Group.id == group_id).first()
            if group:
                existing = db.query(models.GroupSubject).filter(
                    models.GroupSubject.group_id == group_id,
                    models.GroupSubject.subject_id == db_subject.id
                ).first()
                
                if not existing:
                    group_subject = models.GroupSubject(
                        group_id=group_id,
                        subject_id=db_subject.id
                    )
                    db.add(group_subject)
                    logger.info(f"Subject assigned to group {group_id}")
        
        db.commit()
        db.refresh(db_subject)
        
        logger.info(f"Subject created successfully with assignments: {db_subject.id}")
        
        return {
            "id": db_subject.id,
            "name": db_subject.name,
            "total_hours": db_subject.total_hours,
            "hours_per_week": db_subject.hours_per_week,
            "subject_type": db_subject.subject_type,
            "teacher_assigned": teacher_id is not None,
            "group_assigned": group_id is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subject with assignments: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/subjects")
def get_subjects(db: Session = Depends(get_db)):
    try:
        return db.query(models.Subject).all()
    except Exception as e:
        logger.error(f"Error getting subjects: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    try:
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        db.delete(subject)
        db.commit()
        return {"message": "Subject deleted", "id": subject_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subject: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Teacher-Subject assignment endpoints
@app.post("/api/teacher-subjects")
def assign_subject_to_teacher(
    assignment: TeacherSubjectCreate,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Assigning subject {assignment.subject_id} to teacher {assignment.teacher_id}")
        
        teacher = db.query(models.Teacher).filter(models.Teacher.id == assignment.teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        subject = db.query(models.Subject).filter(models.Subject.id == assignment.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        existing = db.query(models.TeacherSubject).filter(
            models.TeacherSubject.teacher_id == assignment.teacher_id,
            models.TeacherSubject.subject_id == assignment.subject_id
        ).first()
        
        if existing:
            return {"message": "Связь уже существует", "id": existing.id}
        
        db_assignment = models.TeacherSubject(
            teacher_id=assignment.teacher_id,
            subject_id=assignment.subject_id
        )
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        
        logger.info(f"Assignment created successfully: {db_assignment.id}")
        return {"success": True, "message": "Предмет назначен преподавателю", "id": db_assignment.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning subject: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/teacher-subjects")
def remove_subject_from_teacher(
    teacher_id: int,
    subject_id: int,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Removing subject {subject_id} from teacher {teacher_id}")
        
        assignment = db.query(models.TeacherSubject).filter(
            models.TeacherSubject.teacher_id == teacher_id,
            models.TeacherSubject.subject_id == subject_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Связь не найдена")
        
        db.delete(assignment)
        db.commit()
        
        logger.info("Assignment removed successfully")
        return {"success": True, "message": "Связь удалена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing assignment: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/teachers-with-subjects")
def get_teachers_with_subjects(db: Session = Depends(get_db)):
    try:
        teachers = db.query(models.Teacher).all()
        result = []
        
        for teacher in teachers:
            subject_ids = [ts.subject_id for ts in teacher.subjects]
            result.append({
                "id": teacher.id,
                "name": teacher.name,
                "department": teacher.department,
                "max_hours_per_week": teacher.max_hours_per_week,
                "subject_ids": subject_ids
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting teachers with subjects: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Group-Subject assignment endpoints
@app.post("/api/group-subjects")
def assign_subject_to_group(
    assignment: GroupSubjectCreate,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Assigning subject {assignment.subject_id} to group {assignment.group_id}")
        
        group = db.query(models.Group).filter(models.Group.id == assignment.group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        subject = db.query(models.Subject).filter(models.Subject.id == assignment.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        existing = db.query(models.GroupSubject).filter(
            models.GroupSubject.group_id == assignment.group_id,
            models.GroupSubject.subject_id == assignment.subject_id
        ).first()
        
        if existing:
            return {"message": "Связь уже существует", "id": existing.id}
        
        db_assignment = models.GroupSubject(
            group_id=assignment.group_id,
            subject_id=assignment.subject_id
        )
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        
        logger.info(f"Group-subject assignment created: {db_assignment.id}")
        return {"success": True, "message": "Предмет назначен группе", "id": db_assignment.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning subject to group: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/group-subjects")
def remove_subject_from_group(
    group_id: int,
    subject_id: int,
    db: Session = Depends(get_db)
):
    try:
        assignment = db.query(models.GroupSubject).filter(
            models.GroupSubject.group_id == group_id,
            models.GroupSubject.subject_id == subject_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Связь не найдена")
        
        db.delete(assignment)
        db.commit()
        
        return {"success": True, "message": "Предмет удален у группы"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing subject from group: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/groups-with-subjects")
def get_groups_with_subjects(db: Session = Depends(get_db)):
    try:
        groups = db.query(models.Group).all()
        result = []
        
        for group in groups:
            subject_ids = [gs.subject_id for gs in group.subjects]
            result.append({
                "id": group.id,
                "name": group.name,
                "course": group.course,
                "students_count": group.students_count,
                "subject_ids": subject_ids
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting groups with subjects: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Schedule generation endpoint
@app.post("/api/schedule/generate-for-period")
def generate_schedule_for_period(
    request: SchedulePeriodRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Generate request received: {request}")
        
        scheduler = AutoScheduler(db)
        
        # Определяем даты периода
        if request.period_type == 'week':
            if request.period_value:
                try:
                    start_date = datetime.strptime(request.period_value, '%Y-%m-%d').date()
                except:
                    today = date.today()
                    start_date = today - timedelta(days=today.weekday())
            else:
                today = date.today()
                start_date = today - timedelta(days=today.weekday())
            
            end_date = start_date + timedelta(days=4)
            logger.info(f"Week period: {start_date} - {end_date}")
            
        elif request.period_type == 'month':
            if request.period_value:
                try:
                    year, month = map(int, request.period_value.split('-'))
                    start_date = date(year, month, 1)
                    if month == 12:
                        end_date = date(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = date(year, month + 1, 1) - timedelta(days=1)
                except:
                    today = date.today()
                    start_date = date(today.year, today.month, 1)
                    if today.month == 12:
                        end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            else:
                today = date.today()
                start_date = date(today.year, today.month, 1)
                if today.month == 12:
                    end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            
            logger.info(f"Month period: {start_date} - {end_date}")
        else:
            raise HTTPException(status_code=400, detail="Неверный тип периода")
        
        result = scheduler.generate_schedule_for_period(
            start_date=start_date,
            end_date=end_date
        )
        
        if isinstance(result, dict):
            result['period'] = {
                'type': request.period_type,
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Get schedule table
@app.get("/api/schedule/table")
def get_schedule_table(
    start_date: str = Query(..., description="Начальная дата (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Конечная дата (YYYY-MM-DD)"),
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить расписание в виде таблицы для отображения"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        exporter = ScheduleExporter(db)
        table_data = exporter.create_schedule_table(start, end, group_id)
        
        return table_data
    except Exception as e:
        logger.error(f"Error getting schedule table: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Available periods
@app.get("/api/available-periods")
def get_available_periods(db: Session = Depends(get_db)):
    try:
        today = date.today()
        
        # Текущая неделя (пн-пт)
        current_week_start = today - timedelta(days=today.weekday())
        current_week_end = current_week_start + timedelta(days=4)
        
        # Текущий месяц
        current_month_start = date(today.year, today.month, 1)
        if today.month == 12:
            current_month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            current_month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        return {
            'current_week': {
                'start': current_week_start.strftime('%Y-%m-%d'),
                'end': current_week_end.strftime('%Y-%m-%d')
            },
            'current_month': {
                'start': current_month_start.strftime('%Y-%m-%d'),
                'end': current_month_end.strftime('%Y-%m-%d')
            }
        }
    except Exception as e:
        logger.error(f"Error getting available periods: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Export endpoints
@app.get("/api/export/excel")
def export_excel(
    start_date: str = Query(..., description="Начальная дата (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Конечная дата (YYYY-MM-DD)"),
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Экспорт расписания в Excel"""
    try:
        logger.info(f"Exporting Excel for period: {start_date} - {end_date}, group_id={group_id}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        exporter = ScheduleExporter(db)
        excel_file = exporter.export_to_excel(start, end, group_id)
        
        filename = f"schedule_{start_date}_to_{end_date}.xlsx"
        
        return Response(
            content=excel_file.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export/pdf")
def export_pdf(
    start_date: str = Query(..., description="Начальная дата (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Конечная дата (YYYY-MM-DD)"),
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Экспорт расписания в PDF"""
    try:
        logger.info(f"Exporting PDF for period: {start_date} - {end_date}, group_id={group_id}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        exporter = ScheduleExporter(db)
        pdf_file = exporter.export_to_pdf(start, end, group_id)
        
        filename = f"schedule_{start_date}_to_{end_date}.pdf"
        
        return Response(
            content=pdf_file.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# Clear schedule
@app.delete("/api/schedule/clear")
def clear_schedule(db: Session = Depends(get_db)):
    try:
        count = db.query(models.Schedule).delete()
        db.commit()
        return {"message": f"Schedule cleared, {count} entries deleted"}
    except Exception as e:
        logger.error(f"Error clearing schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Stats endpoint
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        stats = {
            "groups": db.query(models.Group).count(),
            "teachers": db.query(models.Teacher).count(),
            "subjects": db.query(models.Subject).count(),
            "schedule_pairs": db.query(models.Schedule).count(),
            "total_hours": db.query(models.Schedule).count() * 2
        }
        logger.info(f"Stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "groups": 0,
            "teachers": 0,
            "subjects": 0,
            "schedule_pairs": 0,
            "total_hours": 0
        }