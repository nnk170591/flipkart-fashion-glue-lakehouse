#!/usr/bin/env python3
import aws_cdk as cdk
from flipkart_fashion_glue_lakehouse_stack import (
    FlipkartFashionGlueLakehouseStack,
)

app = cdk.App()

FlipkartFashionGlueLakehouseStack(app, "FlipkartFashionGlueLakehouseStack")

env = cdk.Environment(account="512317193768", region="us-east-1")


app.synth()