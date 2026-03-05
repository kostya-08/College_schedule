# backend/app/scheduler.py
import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from .models import Group, Teacher, Subject, Schedule, Semester, GroupSubject, TeacherSubject
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoScheduler:
    def __init__(self, db: Session):
        self.db = db
        # Время начала и конца пар
        self.time_slots = [
            {"start": "08:40", "end": "10:00", "num": 1},
            {"start": "10:10", "end": "11:30", "num": 2},
            {"start": "12:00", "end": "13:20", "num": 3},
            {"start": "13:30", "end": "14:50", "num": 4},
            {"start": "15:00", "end": "16:20", "num": 5},
            {"start": "16:30", "end": "17:50", "num": 6}
        ]
        self.days_of_week = [0, 1, 2, 3, 4]  # пн-пт
        
        # Аудитории
        self.rooms = ["102", "103", "104"]
        
        # Праздники
        self.holidays = ["01-01", "01-07", "02-23", "03-08", "05-01", "05-09", "06-12", "11-04"]
    
    def get_group_course(self, group_name: str) -> int:
        """Определить курс группы по названию"""
        if group_name.endswith('1'):
            return 1
        elif group_name.endswith('2'):
            return 2
        return 0
    
    def get_group_type(self, group_name: str) -> str:
        """Определить тип группы (рпо или кгид)"""
        if 'рпо' in group_name.lower():
            return 'rpo'
        elif 'кгид' in group_name.lower():
            return 'kgid'
        return 'unknown'
    
    def get_teaching_days(self, start_date: date, end_date: date) -> List[date]:
        """Получить все учебные дни в периоде"""
        teaching_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() not in [5, 6]:  # не сб и вс
                if current.strftime('%m-%d') not in self.holidays:
                    teaching_days.append(current)
            current += timedelta(days=1)
        return teaching_days
    
    def get_teachers_for_subject(self, subject_id: int) -> List[Teacher]:
        """Получить преподавателей для предмета"""
        teachers = []
        teacher_subjects = self.db.query(TeacherSubject).filter(
            TeacherSubject.subject_id == subject_id
        ).all()
        
        for ts in teacher_subjects:
            teacher = self.db.query(Teacher).filter(Teacher.id == ts.teacher_id).first()
            if teacher:
                teachers.append(teacher)
        
        return teachers
    
    def get_subjects_for_group(self, group_id: int) -> List[Subject]:
        """Получить предметы группы"""
        group_subjects = self.db.query(GroupSubject).filter(
            GroupSubject.group_id == group_id
        ).all()
        
        subject_ids = [gs.subject_id for gs in group_subjects]
        if not subject_ids:
            return []
        
        subjects = self.db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        return subjects
    
    def check_slot_available(self, day: date, slot_num: int, group_id: int = None, 
                            teacher_id: int = None, room: str = None) -> bool:
        """Проверить доступность слота"""
        slot_time = self.time_slots[slot_num - 1]["start"]
        
        # Проверяем группу
        if group_id:
            busy = self.db.query(Schedule).filter(
                Schedule.group_id == group_id,
                Schedule.date == day,
                Schedule.start_time == slot_time
            ).first()
            if busy:
                return False
        
        # Проверяем преподавателя
        if teacher_id:
            busy = self.db.query(Schedule).filter(
                Schedule.teacher_id == teacher_id,
                Schedule.date == day,
                Schedule.start_time == slot_time
            ).first()
            if busy:
                return False
        
        # Проверяем аудиторию
        if room:
            busy = self.db.query(Schedule).filter(
                Schedule.room == room,
                Schedule.date == day,
                Schedule.start_time == slot_time
            ).first()
            if busy:
                return False
        
        return True
    
    def get_semester_dates(self, semester_id: Optional[int] = None) -> Tuple[date, date]:
        """Получить даты семестра"""
        try:
            if semester_id:
                semester = self.db.query(Semester).filter(Semester.id == semester_id).first()
                if semester:
                    return semester.start_date, semester.end_date
            
            today = date.today()
            if today.month >= 8:
                start_date = date(today.year, 9, 1)
                end_date = date(today.year + 1, 1, 15)
            elif today.month >= 2:
                start_date = date(today.year, 2, 9)
                end_date = date(today.year, 6, 30)
            else:
                start_date = date(today.year - 1, 9, 1)
                end_date = date(today.year, 1, 15)
            
            return start_date, end_date
        except Exception as e:
            logger.error(f"Error in get_semester_dates: {e}")
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            return start_date, end_date
    
    def generate_schedule_for_period(self, 
                                    semester_id: Optional[int] = None, 
                                    start_date: Optional[date] = None, 
                                    end_date: Optional[date] = None) -> Dict:
        """
        Генерация полного расписания для всех групп
        Каждая группа получает 6 пар в день
        """
        try:
            logger.info("=" * 60)
            logger.info("STARTING SCHEDULE GENERATION")
            logger.info("=" * 60)
            
            # Получаем все группы
            all_groups = self.db.query(Group).all()
            logger.info(f"Found {len(all_groups)} groups: {[g.name for g in all_groups]}")
            
            if not all_groups:
                return {"error": "Нет групп в базе данных"}
            
            # Определяем даты периода
            if not start_date or not end_date:
                start_date, end_date = self.get_semester_dates(semester_id)
            
            logger.info(f"Period: {start_date} - {end_date}")
            
            teaching_days = self.get_teaching_days(start_date, end_date)
            if not teaching_days:
                return {"error": "Нет учебных дней в выбранном периоде"}
            
            logger.info(f"Teaching days: {len(teaching_days)}")
            
            # Очищаем старое расписание за этот период
            deleted = self.db.query(Schedule).filter(
                Schedule.date >= start_date,
                Schedule.date <= end_date
            ).delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {deleted} existing schedule entries")
            
            new_schedule = []
            
            # Словари для отслеживания оставшихся часов по предметам
            remaining_hours = {}
            
            # Проверяем, есть ли предметы у групп
            groups_with_subjects = []
            for group in all_groups:
                subjects = self.get_subjects_for_group(group.id)
                if subjects:
                    groups_with_subjects.append(group)
                    for subject in subjects:
                        key = f"{group.id}_{subject.id}"
                        remaining_hours[key] = subject.total_hours
                        logger.info(f"Group {group.name}, Subject {subject.name}: {subject.total_hours} hours")
                else:
                    logger.warning(f"Group {group.name} has no subjects assigned")
            
            if not groups_with_subjects:
                return {"error": "У групп нет назначенных предметов"}
            
            # Статистика по парам
            pairs_count = {group.id: 0 for group in groups_with_subjects}
            
            # Для каждого учебного дня
            for day_idx, day in enumerate(teaching_days):
                logger.info(f"\nDay {day_idx + 1}/{len(teaching_days)}: {day.strftime('%d.%m.%Y')}")
                
                # ДЛЯ КАЖДОЙ ГРУППЫ проходим по всем слотам
                for group in groups_with_subjects:
                    logger.info(f"  Scheduling {group.name}")
                    
                    # Для каждого временного слота (1-6)
                    for slot_num in range(1, 7):
                        # Получаем доступные предметы для этой группы
                        available_subjects = []
                        subjects = self.get_subjects_for_group(group.id)
                        
                        for subject in subjects:
                            key = f"{group.id}_{subject.id}"
                            if remaining_hours.get(key, 0) > 0:
                                available_subjects.append(subject)
                        
                        if not available_subjects:
                            logger.warning(f"    No subjects with remaining hours for {group.name}")
                            continue
                        
                        # Выбираем случайный предмет
                        subject = random.choice(available_subjects)
                        
                        # Ищем преподавателя
                        teachers = self.get_teachers_for_subject(subject.id)
                        if not teachers:
                            logger.warning(f"    No teachers for subject {subject.name}")
                            continue
                        
                        teacher = random.choice(teachers)
                        
                        # Определяем целевую аудиторию по типу группы
                        group_type = self.get_group_type(group.name)
                        course = self.get_group_course(group.name)
                        
                        if group_type == 'rpo' and course == 2:
                            target_room = "103"  # РПО2 в 103
                        elif group_type == 'kgid' and course == 2:
                            target_room = "102"  # КГИД2 в 102
                        else:
                            target_room = "104"  # Все остальные в 104
                        
                        # Проверяем, свободна ли целевая аудитория
                        if self.check_slot_available(day, slot_num, group.id, teacher.id, target_room):
                            # Ставим пару
                            slot_time = self.time_slots[slot_num - 1]
                            
                            new_schedule.append({
                                'group_id': group.id,
                                'teacher_id': teacher.id,
                                'subject_id': subject.id,
                                'date': day,
                                'day_of_week': day.weekday(),
                                'start_time': slot_time["start"],
                                'end_time': slot_time["end"],
                                'room': target_room,
                                'week_type': 'all',
                                'semester': 1
                            })
                            
                            # Обновляем оставшиеся часы
                            key = f"{group.id}_{subject.id}"
                            remaining_hours[key] = remaining_hours.get(key, 0) - 2
                            
                            # Обновляем статистику
                            pairs_count[group.id] += 1
                            
                            logger.info(f"    Slot {slot_num}: {subject.name} in {target_room}")
                        else:
                            # Если целевая аудитория занята, пробуем другие
                            for room in self.rooms:
                                if room == target_room:
                                    continue
                                if self.check_slot_available(day, slot_num, group.id, teacher.id, room):
                                    slot_time = self.time_slots[slot_num - 1]
                                    new_schedule.append({
                                        'group_id': group.id,
                                        'teacher_id': teacher.id,
                                        'subject_id': subject.id,
                                        'date': day,
                                        'day_of_week': day.weekday(),
                                        'start_time': slot_time["start"],
                                        'end_time': slot_time["end"],
                                        'room': room,
                                        'week_type': 'all',
                                        'semester': 1
                                    })
                                    key = f"{group.id}_{subject.id}"
                                    remaining_hours[key] = remaining_hours.get(key, 0) - 2
                                    pairs_count[group.id] += 1
                                    logger.info(f"    Slot {slot_num}: {subject.name} in {room} (alternative)")
                                    break
                            else:
                                logger.warning(f"    Slot {slot_num}: No available rooms for {group.name}")
            
            # Сохраняем расписание
            if not new_schedule:
                return {"error": "Не удалось создать ни одной пары"}
            
            for entry in new_schedule:
                self.db.add(Schedule(**entry))
            
            self.db.commit()
            
            # Итоговая статистика
            logger.info("\n" + "=" * 60)
            logger.info("SCHEDULE GENERATION COMPLETED")
            logger.info(f"Total pairs: {len(new_schedule)}")
            
            expected_pairs = len(groups_with_subjects) * len(teaching_days) * 6
            logger.info(f"Expected pairs: {expected_pairs}")
            logger.info(f"Coverage: {len(new_schedule)/expected_pairs*100:.1f}%")
            
            for group in groups_with_subjects:
                count = pairs_count[group.id]
                expected = len(teaching_days) * 6
                percentage = (count / expected) * 100 if expected > 0 else 0
                logger.info(f"{group.name}: {count}/{expected} pairs ({percentage:.1f}%)")
            
            logger.info("=" * 60)
            
            return {
                "success": True,
                "message": f"✅ Создано {len(new_schedule)} пар",
                "stats": {
                    "total_pairs": len(new_schedule),
                    "groups_count": len(groups_with_subjects),
                    "teaching_days": len(teaching_days),
                    "period_start": start_date.strftime('%Y-%m-%d'),
                    "period_end": end_date.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            logger.error(f"Error in generate_schedule_for_period: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return {"error": f"Ошибка при генерации: {str(e)}"}