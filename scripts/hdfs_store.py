try:
    from zipfile import ZipFile
    from pyspark import SparkContext, SparkConf
    from pyspark.sql import SparkSession
    import pyspark.sql.functions as f
    import os
except Exception as e:
    print(e)

## http://www.hongyusu.com/imt/technology/spark-via-python-basic-setup-count-lines-and-word-counts.html
def push_acc():
    spark = SparkSession.builder \
    .master('spark://master:7077') \
    .appName("Push Accidents data to HDFS") \
    .getOrCreate()
    sc = spark.sparkContext
    sc.setLogLevel('WARN')
    
    # unzip the file 

   # with ZipFile("/volume/data/accidents_2012_2018.zip", 'r') as zipObj:
       # zipObj.extractall('/volume/data')
       
    # read the data from the volume
    
    acc_data = spark.read.csv("/volume/data/")
    
    # push the data on HDFS as parquet
    
    acc_data.write.parquet("hdfs://hadoop/acc_data_parquet")
   
if __name__ == "__main__":
    push_acc()
