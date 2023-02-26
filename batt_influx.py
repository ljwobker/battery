#!/usr/bin/python3

from datetime import datetime
from dotenv import load_dotenv
import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS




class InfluxClient:
    def __init__(self,token,org,bucket): 

        self._org=org 
        self._bucket = bucket
        self._client = InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com", token=token)

    def write_data(self,data,write_option=SYNCHRONOUS):
        write_api = self._client.write_api(write_option)
        write_api.write(self._bucket, self._org, data, write_precision='s')





