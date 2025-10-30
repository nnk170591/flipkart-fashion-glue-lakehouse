from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_glue as glue,
    aws_s3_assets as s3_assets,
    RemovalPolicy,
)
from constructs import Construct


class FlipkartFashionGlueLakehouseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1️⃣  S3 buckets
        self.raw_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name="flipkart-fashion-raw-data",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.processed_bucket = s3.Bucket(
            self, "ProcessedDataBucket",
            bucket_name="flipkart-fashion-processed-data",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.analytics_bucket = s3.Bucket(
            self, "AnalyticsBucket",
            bucket_name="flipkart-fashion-analytics-data",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # 2️⃣  IAM Role
        self.glue_role = iam.Role(
            self, "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        # 3️⃣  Glue Database
        self.glue_db = glue.CfnDatabase(
            self, "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="flipkart_fashion_db",
                description="Glue catalog database for Flipkart Fashion project",
            ),
        )

        # 🧭 4️⃣  Glue Crawler
        self.raw_crawler = glue.CfnCrawler(
            self, "RawDataCrawler",
            name="flipkart_raw_crawler",
            role=self.glue_role.role_arn,
            database_name="flipkart_fashion_db",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://{self.raw_bucket.bucket_name}/"
                )]
            ),
            description="Crawler to discover schema of raw Flipkart fashion CSV files",
        )

        # 🧮 5️⃣  Raw → Bronze Job
        raw_script_asset = s3_assets.Asset(
            self, "RawToBronzeScript",
            path="glue_jobs/src/raw_to_bronze.py"
        )

        self.raw_to_bronze_job = glue.CfnJob(
            self, "RawToBronzeJob",
            name="flipkart_raw_to_bronze_job",
            role=self.glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{raw_script_asset.s3_bucket_name}/{raw_script_asset.s3_object_key}",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-continuous-cloudwatch-log": "true",
                "--raw_bucket": self.raw_bucket.bucket_name,
                "--processed_bucket": self.processed_bucket.bucket_name,
                "--TempDir": f"s3://{self.processed_bucket.bucket_name}/temp/",
            },
            max_capacity=2.0,
            glue_version="3.0",
            description="ETL job converting raw Flipkart CSVs to cleaned Bronze Parquet",
        )
        raw_script_asset.grant_read(self.glue_role)

        # 🧩 6️⃣  Bronze → Silver Job
        silver_script_asset = s3_assets.Asset(
            self, "BronzeToSilverScript",
            path="glue_jobs/src/bronze_to_silver.py"
        )

        self.bronze_to_silver_job = glue.CfnJob(
            self, "BronzeToSilverJob",
            name="flipkart_bronze_to_silver_job",
            role=self.glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{silver_script_asset.s3_bucket_name}/{silver_script_asset.s3_object_key}",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-continuous-cloudwatch-log": "true",
                "--processed_bucket": self.processed_bucket.bucket_name,
                "--TempDir": f"s3://{self.processed_bucket.bucket_name}/temp/",
            },
            max_capacity=2.0,
            glue_version="3.0",
            description="ETL job transforming Bronze data → Silver zone",
        )
        silver_script_asset.grant_read(self.glue_role)

        # 🧱 7️⃣  Silver → Gold Job (NEW)
        gold_script_asset = s3_assets.Asset(
            self, "SilverToGoldScript",
            path="glue_jobs/src/silver_to_gold.py"
        )

        self.silver_to_gold_job = glue.CfnJob(
            self, "SilverToGoldJob",
            name="flipkart_silver_to_gold_job",
            role=self.glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{gold_script_asset.s3_bucket_name}/{gold_script_asset.s3_object_key}",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-continuous-cloudwatch-log": "true",
                "--processed_bucket": self.processed_bucket.bucket_name,
                "--TempDir": f"s3://{self.processed_bucket.bucket_name}/temp/",
            },
            max_capacity=2.0,
            glue_version="3.0",
            description="ETL job building Gold star schema and aggregates from Silver zone",
        )
        gold_script_asset.grant_read(self.glue_role)

        # 🧩 8️⃣ Glue Workflow
        self.glue_workflow = glue.CfnWorkflow(
            self,
            "FlipkartFashionWorkflow",
            name="flipkart_fashion_etl_workflow",
            description="End-to-end Glue workflow for Flipkart Fashion data pipeline"
        )

        # 🪄 Trigger 1: Start Workflow → RawToBronze
        self.trigger_start = glue.CfnTrigger(
            self,
            "TriggerRawToBronze",
            name="trigger_raw_to_bronze",
            type="ON_DEMAND",
            actions=[glue.CfnTrigger.ActionProperty(job_name=self.raw_to_bronze_job.name)],
            workflow_name=self.glue_workflow.name,
            description="Start Raw → Bronze ETL job"
        )

        # 🪄 Trigger 2: RawToBronze → BronzeToSilver
        self.trigger_bronze_to_silver = glue.CfnTrigger(
            self,
            "TriggerBronzeToSilver",
            name="trigger_bronze_to_silver",
            type="CONDITIONAL",
            start_on_creation=True,
            predicate=glue.CfnTrigger.PredicateProperty(
                conditions=[
                    glue.CfnTrigger.ConditionProperty(
                        logical_operator="EQUALS",
                        job_name=self.raw_to_bronze_job.name,
                        state="SUCCEEDED"
                    )
                ]
            ),
            actions=[glue.CfnTrigger.ActionProperty(job_name=self.bronze_to_silver_job.name)],
            workflow_name=self.glue_workflow.name,
            description="Run Bronze → Silver after Raw → Bronze succeeds"
        )

        # 🪄 Trigger 3: BronzeToSilver → SilverToGold
        self.trigger_silver_to_gold = glue.CfnTrigger(
            self,
            "TriggerSilverToGold",
            name="trigger_silver_to_gold",
            type="CONDITIONAL",
            start_on_creation=True,
            predicate=glue.CfnTrigger.PredicateProperty(
                conditions=[
                    glue.CfnTrigger.ConditionProperty(
                        logical_operator="EQUALS",
                        job_name=self.bronze_to_silver_job.name,
                        state="SUCCEEDED"
                    )
                ]
            ),
            actions=[glue.CfnTrigger.ActionProperty(job_name=self.silver_to_gold_job.name)],
            workflow_name=self.glue_workflow.name,
            description="Run Silver → Gold after Bronze → Silver succeeds"
        )
        self.trigger_silver_to_gold.add_dependency(self.glue_workflow)


        # 🕷️ 7️⃣ Crawlers for processed zones (Bronze, Silver, Gold)
        self.bronze_crawler = glue.CfnCrawler(
            self, "BronzeCrawler",
            name="flipkart_bronze_crawler",
            role=self.glue_role.role_arn,
            database_name="flipkart_fashion_db",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.processed_bucket.bucket_name}/bronze/"
                    )
                ]
            ),
            description="Crawler for Bronze (cleaned raw) Flipkart fashion data",
        )

        self.silver_crawler = glue.CfnCrawler(
            self, "SilverCrawler",
            name="flipkart_silver_crawler",
            role=self.glue_role.role_arn,
            database_name="flipkart_fashion_db",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.processed_bucket.bucket_name}/silver/"
                    )
                ]
            ),
            description="Crawler for Silver (standardized) Flipkart fashion data",
        )

        self.gold_crawler = glue.CfnCrawler(
            self, "GoldCrawler",
            name="flipkart_gold_crawler",
            role=self.glue_role.role_arn,
            database_name="flipkart_fashion_db",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.processed_bucket.bucket_name}/gold/"
                    )
                ]
            ),
            description="Crawler for Gold (aggregated) Flipkart fashion data",
        )


        # ✅ Export outputs (kept at the end)
        self.export_values()
        

        
            

    def export_values(self):
        from aws_cdk import CfnOutput
        CfnOutput(self, "RawBucketName", value=self.raw_bucket.bucket_name)
        CfnOutput(self, "ProcessedBucketName", value=self.processed_bucket.bucket_name)
        CfnOutput(self, "AnalyticsBucketName", value=self.analytics_bucket.bucket_name)
        CfnOutput(self, "GlueRoleArn", value=self.glue_role.role_arn)
        CfnOutput(self, "GlueDatabaseName", value="flipkart_fashion_db")
        CfnOutput(self, "GlueCrawlerName", value="flipkart_raw_crawler")
        CfnOutput(self, "GlueRawToBronzeJob", value="flipkart_raw_to_bronze_job")
        CfnOutput(self, "GlueBronzeToSilverJob", value="flipkart_bronze_to_silver_job")
        CfnOutput(self, "GlueSilverToGoldJob", value="flipkart_silver_to_gold_job") 
        CfnOutput(self, "BronzeCrawlerName", value="flipkart_bronze_crawler")
        CfnOutput(self, "SilverCrawlerName", value="flipkart_silver_crawler")
        CfnOutput(self, "GoldCrawlerName", value="flipkart_gold_crawler")

