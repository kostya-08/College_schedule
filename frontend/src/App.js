import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://127.0.0.1:8000/api';

function App() {
  // Основные состояния
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Для расписания
  const [scheduleDays, setScheduleDays] = useState([]);
  
  // Для выбора периода (только неделя и месяц)
  const [periodType, setPeriodType] = useState('month');
  const [selectedWeek, setSelectedWeek] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [availablePeriods, setAvailablePeriods] = useState({
    current_week: { start: '', end: '' },
    current_month: { start: '', end: '' }
  });
  
  // Для добавления новых элементов
  const [newItem, setNewItem] = useState({
    type: '',
    name: '',
    course: '',
    students_count: '',
    department: '',
    max_hours: 24,
    total_hours: '',
    hours_per_week: '',
    subject_type: 'common',
    teacher_id: '',
    group_id: ''
  });

  // Инициализация при загрузке
  useEffect(() => {
    checkBackendConnection();
    fetchAllData();
  }, []);

  // Проверка подключения к бэкенду
  const checkBackendConnection = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/');
      const data = await res.json();
      console.log('✅ Backend connected:', data);
      setSuccess('✅ Подключение к серверу установлено');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('❌ Не удалось подключиться к серверу. Запустите бэкенд!');
      console.error('Connection error:', err);
    }
  };

  // Загрузка всех данных
  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchGroups(),
        fetchTeachers(),
        fetchSubjects(),
        fetchAvailablePeriods()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Ошибка загрузки данных');
    }
    setLoading(false);
  };

  // Загрузка групп
  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API_URL}/groups`);
      if (res.ok) {
        const data = await res.json();
        setGroups(data);
        console.log('✅ Groups loaded:', data.length);
      }
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  // Загрузка преподавателей
  const fetchTeachers = async () => {
    try {
      const res = await fetch(`${API_URL}/teachers`);
      if (res.ok) {
        const data = await res.json();
        setTeachers(data);
        console.log('✅ Teachers loaded:', data.length);
      }
    } catch (error) {
      console.error('Error fetching teachers:', error);
    }
  };

  // Загрузка предметов
  const fetchSubjects = async () => {
    try {
      const res = await fetch(`${API_URL}/subjects`);
      if (res.ok) {
        const data = await res.json();
        setSubjects(data);
        console.log('✅ Subjects loaded:', data.length);
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  // Загрузка доступных периодов
  const fetchAvailablePeriods = async () => {
    try {
      const res = await fetch(`${API_URL}/available-periods`);
      if (res.ok) {
        const data = await res.json();
        setAvailablePeriods(data);
        
        // Устанавливаем значения по умолчанию
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        
        setSelectedWeek(data.current_week.start);
        setSelectedMonth(`${year}-${month}`);
        
        console.log('✅ Available periods loaded');
      }
    } catch (error) {
      console.error('Error fetching periods:', error);
    }
  };

  // Вспомогательная функция для получения названия месяца
  const getMonthName = (monthNum) => {
    const months = [
      'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ];
    return months[monthNum - 1] || '';
  };

  // Функция для группировки расписания по группам
  const groupScheduleByGroup = () => {
    const groupsData = {};
    
    if (!scheduleDays || scheduleDays.length === 0) {
      return {};
    }
    
    // Словарь для соответствия дней недели
    const dayOrder = {
      'Понедельник': 1,
      'Вторник': 2,
      'Среда': 3,
      'Четверг': 4,
      'Пятница': 5
    };
    
    // Получаем все уникальные даты и группируем по месяцам
    const allDates = scheduleDays.map(day => {
      const [dayNum, monthNum, yearNum] = day.date.split('.');
      return {
        date: day.date,
        dayNum: parseInt(dayNum),
        monthNum: parseInt(monthNum),
        yearNum: parseInt(yearNum),
        dayName: day.day,
        dayOrder: dayOrder[day.day] || 0,
        dayData: day
      };
    });
    
    // Группируем по месяцам
    const monthsMap = {};
    
    allDates.forEach(item => {
      const monthKey = `${item.monthNum}.${item.yearNum}`;
      if (!monthsMap[monthKey]) {
        monthsMap[monthKey] = {
          monthNum: item.monthNum,
          yearNum: item.yearNum,
          monthName: getMonthName(item.monthNum),
          days: {}
        };
      }
      monthsMap[monthKey].days[item.dayNum] = item;
    });
    
    // Для каждого месяца создаем полный календарь с 1 по последнее число
    Object.keys(monthsMap).forEach(monthKey => {
      const month = monthsMap[monthKey];
      const lastDay = new Date(month.yearNum, month.monthNum, 0).getDate();
      
      // Создаем все дни месяца от 1 до lastDay
      for (let dayNum = 1; dayNum <= lastDay; dayNum++) {
        if (!month.days[dayNum]) {
          // Если нет данных для этого дня, создаем пустой день
          const date = new Date(month.yearNum, month.monthNum - 1, dayNum);
          const dayOfWeek = date.getDay();
          
          // Пропускаем выходные (суббота и воскресенье)
          if (dayOfWeek === 0 || dayOfWeek === 6) continue;
          
          const dayNames = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
          const dayName = dayNames[dayOfWeek];
          
          month.days[dayNum] = {
            date: `${dayNum.toString().padStart(2, '0')}.${month.monthNum.toString().padStart(2, '0')}.${month.yearNum}`,
            dayNum: dayNum,
            monthNum: month.monthNum,
            yearNum: month.yearNum,
            dayName: dayName,
            dayOrder: dayOrder[dayName] || 0,
            dayData: {
              date: `${dayNum.toString().padStart(2, '0')}.${month.monthNum.toString().padStart(2, '0')}.${month.yearNum}`,
              day: dayName,
              pairs: []
            }
          };
        }
      }
    });
    
    // Для каждой группы собираем данные по месяцам
    Object.keys(monthsMap).forEach(monthKey => {
      const month = monthsMap[monthKey];
      
      Object.values(month.days).forEach(dayInfo => {
        if (!dayInfo.dayData || !dayInfo.dayData.pairs) return;
        
        dayInfo.dayData.pairs.forEach(pair => {
          if (!pair) return;
          
          // Обрабатываем РПО
          if (pair.rpo && Array.isArray(pair.rpo) && pair.rpo.length > 0) {
            pair.rpo.forEach(item => {
              if (!item || !item.group) return;
              
              const groupName = item.group;
              
              if (!groupsData[groupName]) {
                groupsData[groupName] = {};
              }
              
              if (!groupsData[groupName][monthKey]) {
                groupsData[groupName][monthKey] = {
                  monthName: month.monthName,
                  monthNum: month.monthNum,
                  yearNum: month.yearNum,
                  days: {}
                };
              }
              
              const dayKey = `${dayInfo.dayName} ${dayInfo.dayNum}`;
              
              if (!groupsData[groupName][monthKey].days[dayKey]) {
                groupsData[groupName][monthKey].days[dayKey] = {
                  dayName: dayInfo.dayName,
                  dayNum: dayInfo.dayNum,
                  dayOrder: dayInfo.dayOrder,
                  pairs: {}
                };
              }
              
              if (!groupsData[groupName][monthKey].days[dayKey].pairs[pair.num]) {
                groupsData[groupName][monthKey].days[dayKey].pairs[pair.num] = [];
              }
              
              groupsData[groupName][monthKey].days[dayKey].pairs[pair.num].push({
                subject: item.subject || 'Предмет',
                teacher: item.teacher || 'Преподаватель',
                room: item.room || 'ауд.'
              });
            });
          }
          
          // Обрабатываем КГИД
          if (pair.kgid && Array.isArray(pair.kgid) && pair.kgid.length > 0) {
            pair.kgid.forEach(item => {
              if (!item || !item.group) return;
              
              const groupName = item.group;
              
              if (!groupsData[groupName]) {
                groupsData[groupName] = {};
              }
              
              if (!groupsData[groupName][monthKey]) {
                groupsData[groupName][monthKey] = {
                  monthName: month.monthName,
                  monthNum: month.monthNum,
                  yearNum: month.yearNum,
                  days: {}
                };
              }
              
              const dayKey = `${dayInfo.dayName} ${dayInfo.dayNum}`;
              
              if (!groupsData[groupName][monthKey].days[dayKey]) {
                groupsData[groupName][monthKey].days[dayKey] = {
                  dayName: dayInfo.dayName,
                  dayNum: dayInfo.dayNum,
                  dayOrder: dayInfo.dayOrder,
                  pairs: {}
                };
              }
              
              if (!groupsData[groupName][monthKey].days[dayKey].pairs[pair.num]) {
                groupsData[groupName][monthKey].days[dayKey].pairs[pair.num] = [];
              }
              
              groupsData[groupName][monthKey].days[dayKey].pairs[pair.num].push({
                subject: item.subject || 'Предмет',
                teacher: item.teacher || 'Преподаватель',
                room: item.room || 'ауд.'
              });
            });
          }
        });
      });
    });
    
    return groupsData;
  };

  // Загрузка расписания
  const fetchSchedule = async () => {
    setLoading(true);
    setError('');
    
    try {
      let startDate, endDate;
      
      if (periodType === 'week') {
        startDate = selectedWeek;
        const start = new Date(selectedWeek);
        const end = new Date(start);
        end.setDate(end.getDate() + 4);
        endDate = end.toISOString().split('T')[0];
      } else {
        const [year, month] = selectedMonth.split('-').map(Number);
        startDate = `${year}-${String(month).padStart(2, '0')}-01`;
        const lastDay = new Date(year, month, 0).getDate();
        endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
      }
      
      const url = `${API_URL}/schedule/table?start_date=${startDate}&end_date=${endDate}${selectedGroup ? `&group_id=${selectedGroup}` : ''}`;
      
      const res = await fetch(url);
      
      if (res.ok) {
        const data = await res.json();
        setScheduleDays(data.days || []);
        setSuccess('✅ Расписание загружено');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const errorText = await res.text();
        console.error('Error response:', errorText);
        setError('Ошибка загрузки расписания');
      }
    } catch (error) {
      console.error('Error fetching schedule:', error);
      setError('Ошибка загрузки расписания');
    }
    setLoading(false);
  };

  // Генерация расписания
  const generateSchedule = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      let periodValue = '';
      
      if (periodType === 'week') {
        periodValue = selectedWeek;
      } else {
        periodValue = selectedMonth;
      }
      
      const response = await fetch(`${API_URL}/schedule/generate-for-period`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          period_type: periodType,
          period_value: periodValue,
          group_id: selectedGroup ? parseInt(selectedGroup) : null
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setSuccess(result.message);
        await fetchSchedule();
      } else {
        setError(result.error || 'Ошибка при создании расписания');
      }
    } catch (error) {
      console.error('Error generating schedule:', error);
      setError('Ошибка соединения с сервером');
    }
    setLoading(false);
  };

  // Экспорт в Excel
  const exportToExcel = async () => {
    try {
      setLoading(true);
      
      let startDate, endDate;
      
      if (periodType === 'week') {
        startDate = selectedWeek;
        const start = new Date(selectedWeek);
        const end = new Date(start);
        end.setDate(end.getDate() + 4);
        endDate = end.toISOString().split('T')[0];
      } else {
        const [year, month] = selectedMonth.split('-').map(Number);
        startDate = `${year}-${String(month).padStart(2, '0')}-01`;
        const lastDay = new Date(year, month, 0).getDate();
        endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
      }
      
      const url = `${API_URL}/export/excel?start_date=${startDate}&end_date=${endDate}${selectedGroup ? `&group_id=${selectedGroup}` : ''}`;
      
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`Ошибка экспорта: ${res.status}`);
      }
      
      const blob = await res.blob();
      
      if (blob.size === 0) {
        throw new Error('Получен пустой файл');
      }
      
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `schedule_${startDate}_to_${endDate}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(link.href);
      
      setSuccess('✅ Файл Excel успешно скачан');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      setError(`Ошибка при экспорте: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Экспорт в PDF
  const exportToPDF = async () => {
    try {
      setLoading(true);
      
      let startDate, endDate;
      
      if (periodType === 'week') {
        startDate = selectedWeek;
        const start = new Date(selectedWeek);
        const end = new Date(start);
        end.setDate(end.getDate() + 4);
        endDate = end.toISOString().split('T')[0];
      } else {
        const [year, month] = selectedMonth.split('-').map(Number);
        startDate = `${year}-${String(month).padStart(2, '0')}-01`;
        const lastDay = new Date(year, month, 0).getDate();
        endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
      }
      
      const url = `${API_URL}/export/pdf?start_date=${startDate}&end_date=${endDate}${selectedGroup ? `&group_id=${selectedGroup}` : ''}`;
      
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`Ошибка экспорта: ${res.status}`);
      }
      
      const blob = await res.blob();
      
      if (blob.size === 0) {
        throw new Error('Получен пустой файл');
      }
      
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `schedule_${startDate}_to_${endDate}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(link.href);
      
      setSuccess('✅ PDF файл успешно скачан');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error exporting to PDF:', error);
      setError(`Ошибка при экспорте: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Добавление нового элемента
  const addItem = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      if (!newItem.name) {
        setError('Введите название');
        setLoading(false);
        return;
      }

      switch (newItem.type) {
        case 'group':
          if (!newItem.course || !newItem.students_count) {
            setError('Заполните все поля');
            setLoading(false);
            return;
          }
          
          const groupRes = await fetch(`${API_URL}/groups`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: newItem.name,
              course: parseInt(newItem.course),
              students_count: parseInt(newItem.students_count)
            })
          });
          
          if (!groupRes.ok) {
            const data = await groupRes.json();
            setError(`Ошибка: ${data.detail || 'Неизвестная ошибка'}`);
            setLoading(false);
            return;
          }
          break;
          
        case 'teacher':
          if (!newItem.department) {
            setError('Заполните все поля');
            setLoading(false);
            return;
          }
          
          const teacherRes = await fetch(`${API_URL}/teachers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: newItem.name,
              department: newItem.department,
              max_hours_per_week: parseInt(newItem.max_hours)
            })
          });
          
          if (!teacherRes.ok) {
            const data = await teacherRes.json();
            setError(`Ошибка: ${data.detail || 'Неизвестная ошибка'}`);
            setLoading(false);
            return;
          }
          break;
          
        case 'subject':
          if (!newItem.total_hours || !newItem.hours_per_week) {
            setError('Заполните все поля');
            setLoading(false);
            return;
          }
          
          // Создаем предмет с назначениями за один запрос
          const url = new URL(`${API_URL}/subjects-with-assignments`);
          if (newItem.teacher_id) {
            url.searchParams.append('teacher_id', newItem.teacher_id);
          }
          if (newItem.group_id) {
            url.searchParams.append('group_id', newItem.group_id);
          }
          
          const subjectRes = await fetch(url.toString(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: newItem.name,
              total_hours: parseInt(newItem.total_hours),
              hours_per_week: parseInt(newItem.hours_per_week),
              subject_type: newItem.subject_type
            })
          });
          
          if (!subjectRes.ok) {
            const data = await subjectRes.json();
            setError(`Ошибка: ${data.detail || 'Неизвестная ошибка'}`);
            setLoading(false);
            return;
          }
          
          const result = await subjectRes.json();
          console.log("Created subject with assignments:", result);
          break;
          
        default:
          setError('Выберите тип элемента');
          setLoading(false);
          return;
      }

      setSuccess('✅ Элемент успешно добавлен');
      setNewItem({ 
        type: '', 
        name: '', 
        course: '', 
        students_count: '', 
        department: '', 
        max_hours: 24, 
        total_hours: '', 
        hours_per_week: '', 
        subject_type: 'common',
        teacher_id: '',
        group_id: ''
      });
      await fetchAllData();
      
    } catch (error) {
      console.error('Error adding item:', error);
      setError('Ошибка соединения с сервером');
    }
    setLoading(false);
  };

  // Удаление элемента
  const deleteItem = async (type, id) => {
    if (!window.confirm('Вы уверены?')) return;
    
    try {
      const res = await fetch(`${API_URL}/${type}s/${id}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        setSuccess('✅ Элемент удален');
        await fetchAllData();
      }
    } catch (error) {
      console.error('Error deleting item:', error);
      setError('Ошибка при удалении');
    }
  };

  // Очистка расписания
  const clearSchedule = async () => {
    if (!window.confirm('Очистить всё расписание?')) return;
    
    try {
      await fetch(`${API_URL}/schedule/clear`, { method: 'DELETE' });
      setSuccess('✅ Расписание очищено');
      setScheduleDays([]);
    } catch (error) {
      console.error('Error clearing schedule:', error);
      setError('Ошибка при очистке');
    }
  };

  // Рендер формы добавления
  const renderAddForm = () => {
    switch (newItem.type) {
      case 'group':
        return (
          <div className="form-group">
            <input
              type="text"
              placeholder="Название группы (например: рпо1)"
              value={newItem.name}
              onChange={(e) => setNewItem({...newItem, name: e.target.value})}
            />
            <input
              type="number"
              placeholder="Курс"
              value={newItem.course}
              onChange={(e) => setNewItem({...newItem, course: e.target.value})}
            />
            <input
              type="number"
              placeholder="Кол-во студентов"
              value={newItem.students_count}
              onChange={(e) => setNewItem({...newItem, students_count: e.target.value})}
            />
          </div>
        );
      case 'teacher':
        return (
          <div className="form-group">
            <input
              type="text"
              placeholder="ФИО преподавателя"
              value={newItem.name}
              onChange={(e) => setNewItem({...newItem, name: e.target.value})}
            />
            <input
              type="text"
              placeholder="Кафедра"
              value={newItem.department}
              onChange={(e) => setNewItem({...newItem, department: e.target.value})}
            />
            <input
              type="number"
              placeholder="Макс. часов в неделю"
              value={newItem.max_hours}
              onChange={(e) => setNewItem({...newItem, max_hours: e.target.value})}
            />
          </div>
        );
      case 'subject':
        return (
          <div className="form-group">
            <input
              type="text"
              placeholder="Название предмета (например: Математика)"
              value={newItem.name}
              onChange={(e) => setNewItem({...newItem, name: e.target.value})}
            />
            
            <div className="form-row">
              <input
                type="number"
                placeholder="Всего часов"
                value={newItem.total_hours}
                onChange={(e) => setNewItem({...newItem, total_hours: e.target.value})}
              />
              <input
                type="number"
                placeholder="Часов в неделю"
                value={newItem.hours_per_week}
                onChange={(e) => setNewItem({...newItem, hours_per_week: e.target.value})}
              />
            </div>
            
            <div className="subject-type-selector">
              <label className={`type-option ${newItem.subject_type === 'common' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="subject_type"
                  value="common"
                  checked={newItem.subject_type === 'common'}
                  onChange={(e) => setNewItem({...newItem, subject_type: e.target.value})}
                />
                <span className="type-icon">📚</span>
                <span className="type-label">Общий</span>
              </label>
              
              <label className={`type-option ${newItem.subject_type === 'rpo_profile' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="subject_type"
                  value="rpo_profile"
                  checked={newItem.subject_type === 'rpo_profile'}
                  onChange={(e) => setNewItem({...newItem, subject_type: e.target.value})}
                />
                <span className="type-icon">💻</span>
                <span className="type-label">РПО</span>
              </label>
              
              <label className={`type-option ${newItem.subject_type === 'kgid_profile' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="subject_type"
                  value="kgid_profile"
                  checked={newItem.subject_type === 'kgid_profile'}
                  onChange={(e) => setNewItem({...newItem, subject_type: e.target.value})}
                />
                <span className="type-icon">🎨</span>
                <span className="type-label">КГИД</span>
              </label>
            </div>

            <div className="assignment-fields">
              <h4>Назначение предмета</h4>
              
              <div className="assignment-field">
                <label>Выберите преподавателя:</label>
                <select
                  value={newItem.teacher_id || ''}
                  onChange={(e) => setNewItem({...newItem, teacher_id: e.target.value})}
                  className="assignment-select"
                >
                  <option value="">-- Не выбран --</option>
                  {teachers.map(teacher => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name} ({teacher.department})
                    </option>
                  ))}
                </select>
              </div>

              <div className="assignment-field">
                <label>Выберите группу:</label>
                <select
                  value={newItem.group_id || ''}
                  onChange={(e) => setNewItem({...newItem, group_id: e.target.value})}
                  className="assignment-select"
                >
                  <option value="">-- Не выбрана --</option>
                  {groups.map(group => (
                    <option key={group.id} value={group.id}>
                      {group.name} (курс {group.course})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  // Получаем сгруппированные данные
  const groupedData = groupScheduleByGroup();
  const hasData = Object.keys(groupedData).length > 0;

  return (
    <div className="app">
      <header>
        <h1>🏫 Система составления расписания колледжа</h1>
      </header>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
      
      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      {/* Статистика */}
      <div className="stats">
        <div className="stat-card">
          <h3>Группы</h3>
          <p className="stat-number">{groups.length}</p>
        </div>
        <div className="stat-card">
          <h3>Преподаватели</h3>
          <p className="stat-number">{teachers.length}</p>
        </div>
        <div className="stat-card">
          <h3>Предметы</h3>
          <p className="stat-number">{subjects.length}</p>
        </div>
        <div className="stat-card">
          <h3>Пар в расписании</h3>
          <p className="stat-number">{scheduleDays.reduce((acc, day) => acc + (day.pairs?.length || 0), 0)}</p>
        </div>
      </div>

      {/* Панель управления */}
      <div className="control-panel">
        <h2>📅 Управление расписанием</h2>
        
        <div className="period-selector">
          <div className="period-type">
            <label className={periodType === 'week' ? 'active' : ''}>
              <input
                type="radio"
                value="week"
                checked={periodType === 'week'}
                onChange={(e) => setPeriodType(e.target.value)}
              /> Неделя
            </label>
            <label className={periodType === 'month' ? 'active' : ''}>
              <input
                type="radio"
                value="month"
                checked={periodType === 'month'}
                onChange={(e) => setPeriodType(e.target.value)}
              /> Месяц
            </label>
          </div>

          <div className="period-value">
            {periodType === 'week' && (
              <input
                type="date"
                value={selectedWeek}
                onChange={(e) => setSelectedWeek(e.target.value)}
              />
            )}
            
            {periodType === 'month' && (
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              />
            )}
          </div>

          <select
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value)}
            className="group-select"
          >
            <option value="">Все группы</option>
            {groups.map(g => (
              <option key={g.id} value={g.id}>{g.name}</option>
            ))}
          </select>

          <div className="action-buttons">
            <button 
              className="btn-generate"
              onClick={generateSchedule}
              disabled={loading}
            >
              {loading ? '⏳' : '⚡'} Сгенерировать
            </button>
            
            <button 
              className="btn-excel"
              onClick={exportToExcel}
              disabled={loading}
            >
              📊 Excel
            </button>
            
            <button 
              className="btn-pdf"
              onClick={exportToPDF}
              disabled={loading}
            >
              📄 PDF
            </button>
            
            <button 
              className="btn-clear"
              onClick={clearSchedule}
            >
              🗑️ Очистить
            </button>
          </div>
        </div>
      </div>

      {/* Панель с данными */}
      <div className="data-panel">
        <div className="panel">
          <h2>Группы</h2>
          <div className="add-form">
            <select 
              value={newItem.type}
              onChange={(e) => setNewItem({type: e.target.value, name: ''})}
            >
              <option value="">➕ Действие</option>
              <option value="group">➕ Добавить группу</option>
            </select>
            {newItem.type === 'group' && (
              <>
                {renderAddForm()}
                <button onClick={addItem} disabled={loading}>
                  {loading ? '⏳' : '✅'} Добавить
                </button>
              </>
            )}
          </div>
          <div className="items-list">
            {groups.map(group => (
              <div key={group.id} className="item">
                <span>{group.name} (курс {group.course})</span>
                <button onClick={() => deleteItem('group', group.id)}>🗑️</button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Преподаватели</h2>
          <div className="add-form">
            <select 
              value={newItem.type}
              onChange={(e) => setNewItem({type: e.target.value, name: ''})}
            >
              <option value="">➕ Действие</option>
              <option value="teacher">➕ Добавить преподавателя</option>
            </select>
            {newItem.type === 'teacher' && (
              <>
                {renderAddForm()}
                <button onClick={addItem} disabled={loading}>
                  {loading ? '⏳' : '✅'} Добавить
                </button>
              </>
            )}
          </div>
          <div className="items-list">
            {teachers.map(teacher => (
              <div key={teacher.id} className="item">
                <span>{teacher.name}</span>
                <button onClick={() => deleteItem('teacher', teacher.id)}>🗑️</button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Предметы</h2>
          <div className="add-form">
            <select 
              value={newItem.type}
              onChange={(e) => setNewItem({type: e.target.value, name: ''})}
            >
              <option value="">➕ Действие</option>
              <option value="subject">➕ Добавить предмет</option>
            </select>
            {newItem.type === 'subject' && (
              <>
                {renderAddForm()}
                <button onClick={addItem} disabled={loading}>
                  {loading ? '⏳' : '✅'} Добавить
                </button>
              </>
            )}
          </div>
          <div className="items-list">
            {subjects.map(subject => (
              <div key={subject.id} className="item">
                <span>{subject.name}</span>
                <button onClick={() => deleteItem('subject', subject.id)}>🗑️</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Отображение расписания */}
      <div className="schedule-panel">
        <h2>📋 Расписание на {periodType === 'week' ? 'неделю' : 'месяц'}</h2>
        
        {!hasData ? (
          <div className="no-schedule">
            <p>Расписание пусто</p>
            <p>Выберите период и нажмите "Сгенерировать"</p>
          </div>
        ) : (
          <div className="groups-schedule-vertical">
            {Object.entries(groupedData).map(([groupName, months]) => (
              <div key={groupName} className="group-schedule-card">
                <h3 className="group-title">{groupName}</h3>
                
                {Object.entries(months)
                  .sort((a, b) => {
                    const [monthKeyA, monthDataA] = a;
                    const [monthKeyB, monthDataB] = b;
                    if (monthDataA.yearNum !== monthDataB.yearNum) {
                      return monthDataA.yearNum - monthDataB.yearNum;
                    }
                    return monthDataA.monthNum - monthDataB.monthNum;
                  })
                  .map(([monthKey, monthData]) => {
                    const sortedDays = Object.entries(monthData.days)
                      .sort((a, b) => a[1].dayNum - b[1].dayNum);
                    
                    const isWide = sortedDays.length > 7;
                    
                    return (
                      <div key={monthKey} className="month-schedule">
                        <div className="month-title">{monthData.monthName} {monthData.yearNum}</div>
                        
                        <div className="table-wrapper">
                          <table className={`month-table ${isWide ? 'too-wide' : ''}`}>
                            <thead>
                              <tr>
                                <th>№</th>
                                <th>Время</th>
                                {sortedDays.map(([dayKey, dayData]) => (
                                  <th key={dayKey}>
                                    {dayData.dayName} <span className="day-number">{dayData.dayNum}</span>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {[1, 2, 3, 4, 5, 6].map(pairNum => {
                                const times = {
                                  1: "08:40-10:00",
                                  2: "10:10-11:30",
                                  3: "12:00-13:20",
                                  4: "13:30-14:50",
                                  5: "15:00-16:20",
                                  6: "16:30-17:50"
                                };
                                
                                return (
                                  <tr key={pairNum}>
                                    <td className="pair-num">{pairNum}</td>
                                    <td className="pair-time">{times[pairNum]}</td>
                                    
                                    {sortedDays.map(([dayKey, dayData]) => {
                                      const items = dayData.pairs[pairNum] || [];
                                      
                                      return (
                                        <td key={dayKey} className="pair-cell">
                                          {items.length > 0 ? (
                                            items.map((item, idx) => (
                                              <div key={idx} className="pair-item">
                                                <div className="pair-subject">{item.subject}</div>
                                                <div className="pair-teacher">{item.teacher}</div>
                                                <div className="pair-room">{item.room}</div>
                                              </div>
                                            ))
                                          ) : (
                                            <div className="empty-pair">—</div>
                                          )}
                                        </td>
                                      );
                                    })}
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    );
                  })}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;