# AWS Databricks Real-Time IoT Streaming Pipeline

---

## 🚀 Project Overview

This project implements a scalable, secure **Real-Time IoT Sensor Data Pipeline** leveraging AWS and Databricks. It serves as a **Proof of Concept (PoC)** to demonstrate a full end-to-end cloud-native architecture:

* **Ingestion**: Using **Amazon Kinesis** to capture high-velocity, low-latency sensor data.
* **Processing**: Using **Databricks Structured Streaming** for real-time data transformations.
* **Storage**: Using **Delta Lake** on S3 for a reliable, performant, and transactionally-consistent storage layer.
* **Analysis**: Enabling immediate real-time querying and visualization of the data.

This repository is structured into three main areas: Infrastructure (`cdk_infra`), Processing (`databricks`), and Simulation (`python_iot_simulator`).

---
## Prerequisites and Assumptions

This README provides instructions specific to deploying and running the **IoT Real-Time Data Pipeline** using the provided code. It is not a substitute for official documentation from **AWS** or **Databricks.**

We assume the user has the following accounts and prerequisite configurations already completed:

### Cloud Environment Setup

1. **AWS Account**: Active account with permissions to deploy resources via **AWS CDK** (specifically **IAM**, **S3**, and **Kinesis**).

2. **Databricks Account**: An active **Databricks workspace** (preferably on AWS) with an **All-Purpose Cluster** configured and running.

3. **Unity Catalog Configuration**:

* You have successfully created **Storage Credentials** in **Unity Catalog.**

* Local Environment: **Python 3.9+** and the **AWS CLI** configured locally to deploy the **CDK stack.**

### User Skillset
It is assumed the user is familiar with basic operations within their Databricks workspace, including:

* Creating an **External Location** in **Unity Catalog** that maps to your target S3 bucket (s3://deltalakebucket...).

* Attaching a notebook to a running cluster.

* Running **PySpark** and **%sql** commands.

* Performing basic data visualization and querying using **Databricks SQL.**

---
## 📂 Project Structure

| Directory | Purpose | Key Files |
| :--- | :--- | :--- |
| **cdk_infra** | Infrastructure Deployment (AWS CDK): Defines the Kinesis Stream, the S3 Bucket for the Delta Lake, the Instance Profile for the Databricks EC2 cluster and the corresponding IAM Role. | `cdk_infra_stack.py`, `app.py` |
| **databricks** | Data Processing and Analytics (Databricks): Spark streaming logic and analysis queries. | databricks notebook: `databricks_notebook.py`, `create_schema.sql` data visualization: `query_for_temperature_trend.sql`, `query_for_anomaly_bar_chart.sql` |
| **python_iot_simulator** | Contains the local Python scripts responsible for generating synthetic IoT data. The Producer script uses boto3 to push streaming data to the Kinesis data stream for ingestion testing. A companion Consumer script is also included for local end-to-end verification. | `iot_producer.py`, `iot_consumer.py` |

---

## 🛠️ Setup and Deployment Guide

### A. Local Setup (Python Environment) and Dependency Installation
Navigate to the project root directory `aws_databricks_streaming_project`:

**Step 1: Create the Virtual Environment**

Create a new virtual environment named `.venv`

```bash
python3 -m venv .venv
````
**Step 2: Activate the Virtual Environment**

Activate the virtual environment:

**Linux/macOS:**
```bash
source .venv/bin/activate
````
**Windows (Powershell)**
```bash
.venv\Scripts\Activate.ps1
````
**Step 3: Install dependencies**

Install all necessary packages, including aws-cdk-lib, constructs, and boto3, using the single `requirements.txt` file.

```bash
pip install -r requirements.txt
````

## B. AWS Infrastructure Deployment (CDK)

Once the virtual environment is active and dependencies are installed, you can use the CDK CLI.
Navigate to the `cdk_infra` infrastructure directory:
```bash
# first infra directory
cd cdk_infra
````

Execute the same command one more time to navigate to the nested infrastructure directory where the **cdk stack** resides:

```bash
# nested infra directory
cd cdk_infra
````

### Bootstrap (First Time Only)

If you haven't used CDK in your AWS account/region before, run:

```bash
cdk bootstrap
````
### Synthesize and Deploy

Synthesize the CloudFormation template:

```bash
cdk synth
````

Deploy the stack to your AWS account:

```bash
# Deploy the Kinesis stream, S3Bucket, Instance Profile & IAM role
cdk deploy
````

⚠️ IMPORTANT: Note the outputted Kinesis Stream Name and the IAM Instance Profile ARN (Role). These are required for the next step.

#### Important Note: When finished with the project, you can execute this command to tear down the cdk stack so you don´t incur charges for unutilized resources:
```bash
cdk destroy
````

You can then proceed to deactivate your virual environment:
```bash
deactivate
````

## C. Databricks Configuration

This step links the Databricks cluster to the AWS resources.

Configure Cluster IAM Role:

* In your Databricks Workspace, navigate to Compute.

* Create or edit your cluster.

* Under Advanced Options > Instances, attach the IAM Instance Profile ARN created in the previous step.
This grants the cluster necessary permissions to read from Kinesis.

Import Notebooks and SQL Queries:

* Import the Python notebook `databricks_notebook.py` and the three SQL files into your Databricks workspace.

## D. Execution Workflow

Follow this sequence to initiate the pipeline:

Start Processor (Databricks)

* Open the `create schema.sql` file and run it in the first cell of the notebook to create the managed schema.
* In the second cell of the notebook open and run the imported `databricks_notebook.py` file.
* Ensure configuration variables are correctly set.
* Run the stream writing cell. The Databricks cluster will immediately begin listening for data on Kinesis.

Start Producer (Local):

```bash
cd python_iot_simulator

python iot_producer.py
````
Query Data:

* While the producer and processor are running, use the Databricks SQL Editor to execute the imported SQL query files `query_for_anomaly_bar_chart.sql` and `query_for_temperature_trend.sql` against the resulting Delta Lake table `(iot_sensor_processed)` for real-time analysis and visualization.


### Key Design and Scaling Principles

| Principle | Implementation | Rationale |
| :--- | :--- | :--- |
| **Scaling & Parallelism** | **Kinesis Shards** directly map to **Spark Partitions.** | The number of reading **tasks** scales automatically with the number of Kinesis shards. Increasing Kinesis shards from **1** to **N** will automatically spin up **N** parallel reader tasks within the Databricks cluster. **Node Scaling:** If Databricks auto-scaling is enabled, worker nodes will be added dynamically to ensure sufficient compute power to handle the increased parallelism.|
| **Security (Encryption)** | The AWS SDK (Boto3) enforces TLS/SSL (HTTPS) for all data in transit. Kinesis SSE-KMS & Delta Lake (S3) handle encryption at rest. | **In Transit:** All API calls (producer write, cluster read) are automatically encrypted over HTTPS by the respective AWS SDKs. **At Rest:** Data is protected via Kinesis SSE-KMS and Delta Lake (S3) encryption. |
| **Stream Read Integration** | Use of the Built-in `format("kinesis")` reader. | Leverages the native, optimized Databricks-AWS connector for a stable, low-maintenance stream environment. |
| **Fault Tolerance** | Use of a **Checkpoint Location** in Structured Streaming. | Guarantees **Exactly-Once Processing.** The cluster can safely resume from the last successfully read record in Kinesis following any outage, preventing data loss or duplication. |
| **Data Integrity** | Processing and storage via **Delta Lake**. | Provides crucial **ACID properties** (Atomic, Consistent, Isolated, Durable) and ensures strict schema enforcement on the stored data. |
| **Security (Least Privilege)** | **IAM Instance Profile** attached to the cluster. | Grants the cluster minimal, **read-only permissions** on the Kinesis stream, enforcing a secure operational boundary. |


---
