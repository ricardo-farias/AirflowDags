from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.contrib.kubernetes.secret import Secret

args = {
    'owner': 'Airflow',
    'start_date': days_ago(2)
}

dag = DAG(
    'citi-bike-pipeline',
    default_args=args,
    description='Citi Bike Pipeline',
    schedule_interval=None,
)

aws_access_key_id = Secret('env', 'AWS_ACCESS_KEY_ID', 'citi-bike-secrets', 'aws_access_key_id')
aws_secret_access_key = Secret('env', 'AWS_SECRET_ACCESS_KEY', 'citi-bike-secrets', 'aws_secret_access_key')

# TODO Change this to your ecr dag image
ecr_image = "<dag_ecr_image_url>"

create_cluster_task = KubernetesPodOperator(
    namespace='citi-bike',
    task_id="create_cluster",
    name="create_cluster_task",
    image=ecr_image,
    image_pull_policy='Always',
    arguments=["create_cluster"],
    do_xcom_push=True,
    secrets=[aws_access_key_id, aws_secret_access_key],
    env_vars={'DATA_PRODUCT':'citi_bike'},
    dag=dag
)

configure_job = KubernetesPodOperator(
    namespace='citi-bike',
    task_id="configure_job",
    name="configure_job",
    image=ecr_image,
    image_pull_policy='Always',
    arguments=["configure_job",
    "{{ task_instance.xcom_pull(task_ids='create_cluster', key='return_value')['clusterId'] }}"],
    do_xcom_push=False,
    secrets=[aws_access_key_id, aws_secret_access_key],
    env_vars={'DATA_PRODUCT':'citi_bike'},
    dag=dag
)

spark_submit_task = KubernetesPodOperator(
    namespace='citi-bike',
    task_id="submit_job",
    name="submit_job",
    image=ecr_image,
    image_pull_policy='Always',
    arguments=["submit_job", "{{ task_instance.xcom_pull(task_ids='create_cluster', key='return_value')['clusterId'] }}"],
    do_xcom_push=False,
    secrets=[aws_access_key_id, aws_secret_access_key],
    env_vars={'DATA_PRODUCT':'citi_bike'},
    dag=dag
)

terminate_cluster_task = KubernetesPodOperator(
    namespace='citi-bike',
    name="terminate_job",
    task_id="terminate_job",
    image=ecr_image,
    secrets=[aws_access_key_id, aws_secret_access_key],
    arguments=["terminate_cluster", "{{ task_instance.xcom_pull(task_ids='create_cluster', key='return_value')['clusterId'] }}"],
    in_cluster=True,
    do_xcom_push=False,
    env_vars={'DATA_PRODUCT':'citi_bike'},
    image_pull_policy='Always',
    dag=dag
)

create_cluster_task >> configure_job  >> spark_submit_task >> terminate_cluster_task