try:
    from pyspark import SparkContext, SparkConf
    from pyspark.sql import SparkSession
    import pyspark.sql.functions as f
#    from operator import add
except Exception as e:
    print(e)

## http://www.hongyusu.com/imt/technology/spark-via-python-basic-setup-count-lines-and-word-counts.html
def push_mongo():
    spark = SparkSession \
        .builder \
        .appName("Push to MongoDB") \
        .master("spark://master:7077") \
        .config("spark.mongodb.input.uri", "mongodb://root:password@mongo/test.coll?authSource=admin") \
        .config("spark.mongodb.output.uri", "mongodb://root:password@mongo/test.coll?authSource=admin") \
        .config('spark.jars.packages', 'org.mongodb.spark:mongo-spark-connector_2.11:2.4.0')\
        .getOrCreate()
        
    sc = spark.sparkContext
    sc.setLogLevel('WARN')

    
    
    # Reading Data from volume
    acc_mongo=spark.read.csv("/volume/data")
    
    #Show Mongo data
    acc_mongo.show()
    
    # Store data in MongoDB
    
    acc_mongo.write.format("com.mongodb.spark.sql.DefaultSource").mode("append").save()

    # End the Spark Context
    spark.stop()

if __name__ == "__main__":
    push_mongo()
