#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_infra.cdk_infra_stack import CdkInfraStack

# Initialize the App
app = cdk.App()
CdkInfraStack(app, "CdkInfraStack",)

app.synth()
