"""
Example of using Apache Airflow for slot processing.
Good for complex scheduling and monitoring needs.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

# Would need: pip install apache-airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup

from backend.database import get_db
from tools.docx_parser import DOCXParser
from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService


def fetch_user_slots(**context) -> List[Dict[str, Any]]:
    """Fetch slots for user."""
    user_id = context["dag_run"].conf.get("user_id", "default_user")
    db = get_db()
    slots = db.get_user_slots(user_id)
    
    # Push slots to XCom for other tasks
    task_instance = context['task_instance']
    task_instance.xcom_push(key='slot_count', value=len(slots))
    task_instance.xcom_push(key='slot_ids', value=[s['id'] for s in slots])
    
    return slots


def process_slot(slot_id: str, **context) -> Dict[str, Any]:
    """Process individual slot."""
    dag_run_conf = context["dag_run"].conf
    week_of = dag_run_conf.get("week_of")
    provider = dag_run_conf.get("provider", "openai")
    
    # Get slot details
    db = get_db()
    slot = db.get_slot(slot_id)
    
    if not slot:
        raise ValueError(f"Slot {slot_id} not found")
    
    # Process slot (existing logic)
    processor = BatchProcessor(LLMService(provider))
    result = processor._process_slot(
        slot=slot,
        week_of=week_of,
        provider=provider,
        week_folder_path=dag_run_conf.get("week_folder_path"),
        plan_id=context["dag_run"].run_id
    )
    
    return result


def combine_slots(**context) -> Dict[str, Any]:
    """Combine all processed slots."""
    task_instance = context['task_instance']
    
    # Get all slot results from XCom
    slot_ids = task_instance.xcom_pull(task_ids='fetch_slots', key='slot_ids')
    slot_results = []
    
    for slot_id in slot_ids:
        result = task_instance.xcom_pull(task_ids=f'process_slot_{slot_id}')
        if result:
            slot_results.append(result)
    
    # Combine using existing logic
    if slot_results:
        processor = BatchProcessor(LLMService("openai"))
        combined = processor._combine_lessons(slot_results)
        return combined
    
    return {"success": False, "error": "No slots processed"}


def notify_completion(**context):
    """Send notification when processing completes."""
    task_instance = context['task_instance']
    result = task_instance.xcom_pull(task_ids='combine_slots')
    
    if result.get("success"):
        print(f"✅ Successfully processed {result.get('processed_slots')} slots")
    else:
        print(f"❌ Processing failed: {result.get('error')}")


# Default DAG configuration
default_args = {
    'owner': 'bilingual-plan-builder',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
with DAG(
    dag_id='weekly_lesson_plan_processing',
    default_args=default_args,
    description='Process weekly bilingual lesson plans',
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=['bilingual', 'education', 'lesson-plans'],
) as dag:
    
    # Task 1: Fetch user slots
    fetch_slots = PythonOperator(
        task_id='fetch_slots',
        python_callable=fetch_user_slots
    )
    
    # Task 2: Process each slot (dynamic task group)
    process_slots = TaskGroup('process_slots')
    
    # This would be dynamically generated based on actual slots
    # For demonstration, creating a few example tasks
    process_slot_1 = PythonOperator(
        task_id='process_slot_1',
        python_callable=process_slot,
        op_kwargs={'slot_id': 'slot-1'},
        task_group=process_slots
    )
    
    process_slot_2 = PythonOperator(
        task_id='process_slot_2',
        python_callable=process_slot,
        op_kwargs={'slot_id': 'slot-2'},
        task_group=process_slots
    )
    
    # Task 3: Combine all slots
    combine = PythonOperator(
        task_id='combine_slots',
        python_callable=combine_slots
    )
    
    # Task 4: Notify completion
    notify = PythonOperator(
        task_id='notify_completion',
        python_callable=notify_completion
    )
    
    # Define dependencies
    fetch_slots >> process_slots >> combine >> notify


# Alternative: Dynamic DAG generation based on user configuration
def create_dynamic_dag(user_id: str, slots: List[Dict[str, Any]]):
    """Create a DAG with tasks for each slot."""
    
    with DAG(
        dag_id=f'weekly_plan_{user_id}',
        default_args=default_args,
        description=f'Weekly lesson plan processing for {user_id}',
        schedule_interval=None,
        catchup=False,
    ) as dynamic_dag:
        
        fetch = PythonOperator(
            task_id='fetch_slots',
            python_callable=fetch_user_slots,
            op_kwargs={'user_id': user_id}
        )
        
        # Create dynamic task group for slots
        with TaskGroup('process_slots') as slot_group:
            for slot in slots:
                PythonOperator(
                    task_id=f'process_slot_{slot["id"]}',
                    python_callable=process_slot,
                    op_kwargs={'slot_id': slot["id"]}
                )
        
        combine = PythonOperator(
            task_id='combine_slots',
            python_callable=combine_slots
        )
        
        fetch >> slot_group >> combine
    
    return dynamic_dag
