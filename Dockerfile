FROM puckel/docker-airflow

USER root

COPY airflow.cfg ./airflow.cfg
COPY /dags ./dags

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
RUN pip3 install --upgrade pip

# Add directory in which pip installs to PATH
ENV PATH="/usr/local/airflow/.local/bin:${PATH}"
USER airflow

ENTRYPOINT ["/entrypoint.sh"]

# Just for documentation. Expose webserver, worker and flower respectively
EXPOSE 8080
EXPOSE 8793
EXPOSE 5555