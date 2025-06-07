from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os

def get_text_analytics_client():
    endpoint = os.getenv("AZURE_ENDPOINT")
    key = os.getenv("AZURE_KEY")
    credential = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credential)