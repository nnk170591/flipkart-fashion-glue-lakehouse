import aws_cdk as core
import aws_cdk.assertions as assertions

from flipkart_fashion_glue_lakehouse.flipkart_fashion_glue_lakehouse_stack import FlipkartFashionGlueLakehouseStack

# example tests. To run these tests, uncomment this file along with the example
# resource in flipkart_fashion_glue_lakehouse/flipkart_fashion_glue_lakehouse_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FlipkartFashionGlueLakehouseStack(app, "flipkart-fashion-glue-lakehouse")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
