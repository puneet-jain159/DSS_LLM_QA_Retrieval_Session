# Databricks notebook source
# MAGIC %run "./util/notebook-config"

# COMMAND ----------

qa_log_loc = f'{config["ui_logs"]}/qa_logs/{config["model_id"]}/{config["use-case"]}'
like_log_loc = f'{config["ui_logs"]}/like_logs/{config["model_id"]}/{config["use-case"]}'

qa_inferred_schema_loc = f'{config["ui_logs"]}/qa_inferred_schema/{config["model_id"]}/{config["use-case"]}'
like_inferred_schema_loc = f'{config["ui_logs"]}/like_inferred_schema/{config["model_id"]}/{config["use-case"]}'

qa_checkpoint_loc = f'{config["ui_logs"]}/qa_checkpoint/{config["model_id"]}/{config["use-case"]}'
like_checkpoint_loc = f'{config["ui_logs"]}/like_checkpoint/{config["model_id"]}/{config["use-case"]}'

# COMMAND ----------

# ! rm -rf {config["ui_logs"]}/qa_inferred_schema_loc/{config["model_id"]}/{config["use-case"]}
# !  rm -rf   {config["ui_logs"]}/qa_checkpoint/{config["model_id"]}/{config["use-case"]}


# COMMAND ----------

bronze_qa_log = (spark.readStream \
                .format("cloudFiles")
                .option("cloudFiles.format", "json")
                .option("cloudFiles.schemaLocation", qa_inferred_schema_loc)
                .option("cloudFiles.inferColumnTypes", "true")
                .load(qa_log_loc))
              
_ =  ( bronze_qa_log.writeStream
              .format("delta")
              .option("checkpointLocation", qa_checkpoint_loc)
              .option("mergeSchema", "true")
              .table(f"{config['use-case']}_{config['model_id'].replace('/','_').replace('-','_')}_qa_logs"))

# COMMAND ----------

bronze_likes_log = (spark.readStream \
                .format("cloudFiles")
                .option("cloudFiles.format", "json")
                .option("cloudFiles.schemaLocation", like_inferred_schema_loc)
                .option("cloudFiles.inferColumnTypes", "true")
                .load(like_log_loc))
              
_ =  ( bronze_likes_log.writeStream
              .format("delta")
              .option("checkpointLocation", like_checkpoint_loc)
              .option("mergeSchema", "true")
              .table(f"{config['use-case']}_{config['model_id'].replace('/','_').replace('-','_')}_like_logs"))

# COMMAND ----------

# spark.sql(f"drop table {config['use-case']}_{config['model_id'].replace('/','_').replace('-','_')}_qa_logs")

# COMMAND ----------


