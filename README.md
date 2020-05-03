# Big Data Infrastructure
 
## Contents
- [Collisions Routieres Dataset](#Collisions-Routieres-Dataset)
- [Downloading the data](#Fetching-the-data-and-download-it-into-volume-using-an-image)
- [Creating Volume](#Creating-Volume)
- [Services on Spark Cluster](#Services-on-Spark-Cluster)
- [Preparing Data and Work Environment](#Preparing-Data-and-Work-Environment)
- [Store the data in HDFS and MongoDB](#Store-the-data-in-HDFS-and-MongoDB)
- [Automated Storage](#Automated-Storage)
- [Using Jupyter Notebook](#Using-Jupyter-Notebook)
- [Google Cloud Platform](#Google-Cloud-Platform)
- [The Results Obtained](#The-Results-Obtained)
- [Conclusion](#Conclusion)

## Collisions Routieres Dataset

![pic](./screenshots/Collisions_Routieres_Montreal.png)

### Description

List of collisions that have occurred in Montreal since 2012.

This set includes collisions involving at least one motor vehicle circulating on the network and which have been the subject of a police report. It includes descriptive, contextual and event location information, including seriousness in terms of death, serious injury, minor injury and property damage only.

### Dataset Source

[Collisions Routieres](http://donnees.ville.montreal.qc.ca/dataset/collisions-routieres)

### Dataset Characteristics

Number of Instances: 171,271  
Number of Attributes: 68  
Publishers: Service de l'urbanisme et de la mobilité - Direction de la mobilité  
Frequency of update:  Annual  
Language: French  
Geographic coverage: Territory of the city of Montreal  
Temporal coverage: 2012-01-01 / 2018-12-31  
Last edit: 2019-09-17 09:40  
Created on: 2018-11-11 21:39  
License: Creative Commons Attribution 4.0 International

## Fetching the data and download it into volume using an image
using Dockerfile [data_dockerfile](image_with_data/data_dockerfile) to build an image downloads the data from the source to tmp_data directory then move this data to data directory inside a volume when the container will be created by running the following commands:

```bash
docker build -t database_image -f data_dockerfile .
docker run -it database_image
```

![pic](./image_with_data/data_image.png)

## Creating Volume

### Create Data volume
  
```bash
docker volume create project-scripts-volume
```

### Copy Database to Volume

```bash
docker run --rm -v project-scripts-volume:/volume database_image
```

### Copy Data Folder to Volume

```bash
docker run --rm -v "$(pwd)"/data:/data \
-v project-scripts-volume:/volume busybox \
cp -r /data/ /volume
```
 
### Volume Contents

```bash
docker run -it --rm -v project-scripts-volume:/volume busybox ls -l /volume
```
```bash
docker run -it --rm -v project-scripts-volume:/volume busybox ls -l /volume/data
```
![pic](screenshots/check_volume_content.png)

## Services on Spark Cluster

### Create Spark Network

  Using the following command a spark network will be created as "spark-network"
  
```bash
docker network create spark-network
```

### Spark Cluster with HDFS and MongoDB
using docker compose to create spark cluster by running [spark-compose.yml](./spark-compose.yml) file using the below command:

```bash
env user_mongo=root pass_mongo=password docker-compose --file spark-compose.yml up --scale spark-worker=2
```
## Preparing Data and Work Environment

### Ckecking if the volume accessable by the cluster
- check the containers of the cluster
- execute the worker container to check the volume using the command:

```bash
docker exec -it containerID sh
```
![pic](./screenshots/volume_in_cluster.png)
### Starting Spark Shell

Spark shell will be used to unzip the data inside the volume, upload the data on HDFS and MongoDB.
to start spark shell the below command will be run:
```bash
docker run -it --rm \
  -v project-scripts-volume:/volume \
  --network=spark-network \
  mjhea0/spark:2.4.1 \
  ./bin/pyspark \
  --master spark://master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.11:2.4.0
```
![pic](./screenshots/spark_shell.png)
### Unzip the Data File:
using the following command in spark shell:

```bash
from zipfile import *
with ZipFile("/volume/data/accidents_2012_2018.zip", 'r') as zipObj:
...     zipObj.extractall('/volume/data')
```
![pic](./screenshots/unzip-data.png)

## Store the data in HDFS and MongoDB
### Store the data in HDFS as parquet
first read the unziped data from the volume then push it as parquet into HDFS. to acheive that the following command to be run in spark shell

```bash
acc_data = spark.read.csv("/volume/data")
acc_data.write.parquet("hdfs://hadoop/acc_data_parquet")
```
![pic](./screenshots/hdfs-parquet.png)

to check the data file on HDFS open [http://localhost:50070](http://localhost:50070)  then navigate to "Utilities" in main bar, select "Browse the file system" then the below page will open.

![pic](./screenshots/data_in_hdfs.png)

### Store the data in Mongodb
first in spark shell run the folowing comand to be able pushing the data to MongoDB

```bash
spark = SparkSession \
        .builder \
        .appName("mongodb") \
        .master("spark://master:7077") \
        .config("spark.mongodb.input.uri", "mongodb://root:password@mongo/test.coll?authSource=admin") \
        .config("spark.mongodb.output.uri", "mongodb://root:password@mongo/test.coll?authSource=admin") \
        .config('spark.jars.packages', 'org.mongodb.spark:mongo-spark-connector_2.11:2.4.0')\
        .getOrCreate()
 ```
#### Read the data from the volume and store it in MongoDB

```bash
acc_mongo = spark.read.csv("/volume/data")
acc_mongo.write.format("com.mongodb.spark.sql.DefaultSource").mode("append").save()
```
#### Read the data from the HDFS and store it in MongoDB

```bash
acc_mongo = spark.read.csv("hdfs://hadoop/acc_data_parquet")
acc_mongo.write.format("com.mongodb.spark.sql.DefaultSource").mode("append").save()
```
Open [http://localhost:8181](http://localhost:8181) for Mongo Express.

![pic](./screenshots/mango_express.png)

Then click on "test" for database

![pic](./screenshots/data_in_mongodb.png)

## Automated Storage

### Copy the scripts into the volume
In the volume a directory named "script" will be created and copied all the required scripts into that directory by executing the following command:

```bash
docker run --rm -v "$(pwd)"/scripts:/script \
-v project-scripts-volume:/volume busybox \
cp -r /script/ /volume
```
### Checking the scripts in the volume:

```bash
docker run -it --rm -v project-scripts-volume:/volume busybox ls -l /volume/script
```

![pic](./screenshots/scripts_in_volume.png)
### Store the data in HDFS as parquet
By execute [hdfs_store.py](./scripts/hdfs_store.py) script as following:

```bash
docker run -t --rm \
  -v project-scripts-volume:/volume \
  --network=spark-network \
  mjhea0/spark:2.4.1 \
  bin/spark-submit \
    --master spark://master:7077 \
    --class endpoint \
    /volume/script/hdfs_store.py
```
### Store the data in MongoDB
By execute [mongodb_store.py](./scripts/mongodb_store.py) script as following:

```bash
docker run -t --rm \
  -v project-scripts-volume:/volume \
  --network=spark-network \
  mjhea0/spark:2.4.1 \
  bin/spark-submit \
    --master spark://master:7077 \
    --class endpoint \
    --packages org.mongodb.spark:mongo-spark-connector_2.11:2.4.0 \
    /volume/script/mongodb_store.py
```
## Using Jupyter Notebook
### Create Volume
Creating a volume to store the notbooks Which will be created
```bash
docker volume create notebooks
```

### Jupyter in the Cluster
Keeping the cluster up now to deploy jupyter in cluster using docker compose by running [jupyter-compose.yml](jupyter-compose.yml) file using the below command::
```bash
env TOKEN=project1261 docker-compose --file jupyter-compose.yml up
```
Open http://localhost:8889/?token=project1261

jupyter have access to the volume where the data and scripts are stored.

![pic](./screenshots/jupyter_on_cluster.png)

Openning new notebook and prepare the environment.


### Reading the Data from volume
Read the data from the volume as csv

![pic](./screenshots/read_volume.png)

### Store the Data on HDFS
Push the data to HDFS

![pic](./screenshots/volume_to_hdfs.png)

### Store the Data in MongoDB
Push the data from hdfs into MongoDB

![pic](./screenshots/hdfs_to_mongo.png)

[The Full Notebook](./hdfs_mongo_notebook.ipynb)

## Google Cloud Platform
### Environment Setup

  - First lets create a project.
  
  ![pic](./GCP_Screenshots/create_project.png)
  
  - Enabling the Cloud Dataproc and Google Compute Engine APIs.
  
  - Creating bucket where notebook and the data will be stored.
  
  ![pic](./GCP_Screenshots/create_bucket.png)
  
  ![pic](./GCP_Screenshots/data_in_bucket.png)
  
  - Creating cluster and selecting the the bucket to which was created to have access to the data and where the notebooks will be stored.
  
   ![pic](./GCP_Screenshots/creating_cluster.png)
   
   ![pic](./GCP_Screenshots/add_bucket_to_cluster.png)
   
   In advanced options section Anaconda and jupyter components should be selected to run jupyter in the cluster.
   
   ![pic](./GCP_Screenshots/add_components.png)
   
  - From the web interfaces in created cluster we can open jupyter notebook which is runing on the cluster and have access to the bucket where our data is.
  
  ![pic](./GCP_Screenshots/web_interfaces.png)
  

###  Analytics on GCP

Openning Jupyter on GCP cluster  

![pic](./GCP_Screenshots/run_jupyter_gcp.png)

Running the Project App  
[Exploratory Data Analysis on the Collisions Routieres dataset](./project_app.ipynb)


### Github Mirror and Deploy via GCP
#### Using the exact same process as our local docker stack, we will deploy our application on the GCP. The only difference is that we skip the manual hdfs/mongo-express builds and go right to automated builds.

- Pulling data from github hosted docker image through google shell

![pic](./screenshots/downloading_data.png)


- Running the docker image and making sure the data is in the correct directory

![pic](./screenshots/docker_run.png)


- Copying the scripts

![pic](./screenshots/copying_docker.png)


- Deploying the spark compose file with created network

![pic](./screenshots/docker-compose-up.png)


- Creating jupyter volume

![pic](./screenshots/jupyter_compose.png)


- Jupyter compose up to be able to reach our notebook

![pic](./screenshots/jupyter_up.png)


- Proof of the notebook in action on our GCP project cluster

![pic](./screenshots/working_in_gcp.png)


## The Results Obtained

In our project, we chose to work with the dataset about traffic accidents that happened from 2012 to 2018 in the city of Montreal. We built our infrastructure using a docker container to create an image gathering that dataset from the Montreal Open Data Website. We decompressed, read and wrote the dataset in HDFS (Parquet files) and MongoDB using a spark console running on a Spark Cluster and making use of Docker Volumes. Also, we wrote scripts to make those operations automatically. Plus, we ran a Jupyter Notebook using the same volume where the data was saved and we implemented some exploratory data analysis. The sensitive data as passwords and tokens were handled safely. After doing everything locally as a Docker Stack, we connected our GitHub repository on the Google Cloud Platform and deployed our solution on the Cloud!

## Conclusion

After doing the proposed tutorials during the course classes we could imagine the complexity of Big Data infrastructure. However, after doing the group project, we started to understand such complexity due to the great challenge that was to deploy a simple application both locally and on the Cloud. The use of a lot of structures that characterize Big Data infrastructure solutions can easily become hard work even when we have good tools to help us out.


