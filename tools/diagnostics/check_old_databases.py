from sqlmodel import create_engine, select, Session
from backend.schema import ScheduleEntry, WeeklyPlan
from pathlib import Path

databases = [
    'data/lesson_planner.db',
    'data/lesson_plans.db',
    'data/demo_tracking.db',
    'data/test_lesson_planner.db'
]

new_user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
old_user_id = 'edcde77c-b14f-4296-9017-b26b0b9a369d'
w47_week = '11-17-11-21'

for db_path in databases:
    db_file = Path(db_path)
    if not db_file.exists():
        print(f'\n{db_path}: NOT FOUND')
        continue
    
    print(f'\n{"="*60}')
    print(f'Checking: {db_path}')
    print(f'{"="*60}')
    
    try:
        engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
        session = Session(engine)
        
        # Check schedule entries
        all_schedules = list(session.exec(select(ScheduleEntry)))
        print(f'\nSchedule entries: {len(all_schedules)}')
        
        if all_schedules:
            # Check for Wilson's entries
            wilson_schedules = [s for s in all_schedules if s.user_id in [new_user_id, old_user_id]]
            print(f'  Wilson schedules: {len(wilson_schedules)}')
            if wilson_schedules:
                for s in wilson_schedules[:5]:
                    print(f'    {s.day_of_week} {s.start_time}-{s.end_time}: {s.subject} {s.grade} {s.homeroom}')
        
        # Check W47 plans
        all_plans = list(session.exec(select(WeeklyPlan)))
        print(f'\nWeekly plans: {len(all_plans)}')
        
        w47_plans = [p for p in all_plans if p.week_of == w47_week]
        print(f'  W47 plans (11-17-11-21): {len(w47_plans)}')
        
        if w47_plans:
            for p in w47_plans:
                print(f'    ID: {p.id}')
                print(f'    User: {p.user_id}')
                print(f'    Status: {p.status}')
                print(f'    Output: {p.output_file}')
                print(f'    Has lesson_json: {p.lesson_json is not None}')
        
        # Check Wilson's plans
        wilson_plans = [p for p in all_plans if p.user_id in [new_user_id, old_user_id]]
        print(f'\n  Wilson plans: {len(wilson_plans)}')
        
        session.close()
    except Exception as e:
        print(f'ERROR reading {db_path}: {e}')

