import boto3
import json
import datetime
import time
import sys
import argparse
from colorama import Fore

REGION = ''
USER_POOL_ID = ''
LIMIT = 60
MAX_NUMBER_RECORDS = 0
REQUIRED_ATTRIBUTE = None
JSON_FILE_NAME = 'CognitoUsers.json'
PROFILE = ''
STARTING_TOKEN = ''

""" Parse All Provided Arguments """
parser = argparse.ArgumentParser(description='Cognito User Pool export records to JSON file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-attr', '--export-attributes', nargs='+', type=str, help="List of Attributes to be saved in JSON", required=True)
parser.add_argument('--user-pool-id', type=str, help="The user pool ID", required=True)
parser.add_argument('--region', type=str, default='us-east-1', help="The user pool region")
parser.add_argument('--profile', type=str, default='', help="The aws profile")
parser.add_argument('--starting-token', type=str, default='', help="Starting pagination token")
parser.add_argument('-f', '--file-name', type=str, help="JSON File name")
parser.add_argument('--num-records', type=int, help="Max Number of Cognito Records to be exported")
args = parser.parse_args()

if args.export_attributes:
    REQUIRED_ATTRIBUTE = list(args.export_attributes)
if args.user_pool_id:
    USER_POOL_ID = args.user_pool_id
if args.region:
    REGION = args.region
if args.file_name:
    JSON_FILE_NAME = args.file_name
if args.num_records:
    MAX_NUMBER_RECORDS = args.num_records
if args.profile:
    PROFILE = args.profile
if args.starting_token:
    STARTING_TOKEN = args.starting_token

def datetimeconverter(o):
    if isinstance(o, datetime.datetime):
        return str(o)

def get_list_cognito_users(cognito_idp_client, next_pagination_token='', Limit=LIMIT):
    return cognito_idp_client.list_users(
        UserPoolId=USER_POOL_ID,
        Limit=Limit,
        PaginationToken=next_pagination_token
    ) if next_pagination_token else cognito_idp_client.list_users(
        UserPoolId=USER_POOL_ID,
        Limit=Limit
    )

if PROFILE:
    session = boto3.Session(profile_name=PROFILE)
    client = session.client('cognito-idp', REGION)
else:
    client = boto3.client('cognito-idp', REGION)

try:
    json_file = open(JSON_FILE_NAME, 'w', encoding="utf-8")
except Exception as err:
    error_message = repr(err)
    print(Fore.RED + "\nERROR: Can not create file: " + JSON_FILE_NAME)
    print("\tError Reason: " + error_message)
    exit()

pagination_counter = 0
exported_records_counter = 0
pagination_token = STARTING_TOKEN

all_users = []

while pagination_token is not None:
    try:
        user_records = get_list_cognito_users(
            cognito_idp_client=client,
            next_pagination_token=pagination_token,
            Limit=LIMIT if LIMIT < MAX_NUMBER_RECORDS else MAX_NUMBER_RECORDS
        )
    except client.exceptions.ClientError as err:
        error_message = err.response["Error"]["Message"]
        print(Fore.RED + "Please Check your Cognito User Pool configs")
        print("Error Reason: " + error_message)
        json_file.close()
        exit()
    except Exception as err:
        print(Fore.RED + "Something else went wrong")
        print("Error Reason: " + str(err))
        json_file.close()
        exit()

    if set(["PaginationToken", "NextToken"]).intersection(set(user_records)):
        pagination_token = user_records['PaginationToken'] if "PaginationToken" in user_records else user_records['NextToken']
    else:
        pagination_token = None

    for user in user_records['Users']:
        user_data = {}
        for requ_attr in REQUIRED_ATTRIBUTE:
            user_data[requ_attr] = ''
            if requ_attr in user:
                user_data[requ_attr] = str(user[requ_attr])
                continue
            for usr_attr in user['Attributes']:
                if usr_attr['Name'] == requ_attr:
                    user_data[requ_attr] = str(usr_attr['Value'])

        all_users.append(user_data)

    pagination_counter += 1
    exported_records_counter += len(user_records['Users'])
    print(Fore.YELLOW + "Page: #{} \n Total Exported Records: #{} \n".format(str(pagination_counter), str(exported_records_counter)))

    if MAX_NUMBER_RECORDS and exported_records_counter >= MAX_NUMBER_RECORDS:
        print(Fore.GREEN + "INFO: Max Number of Exported Records Reached")
        break

    if pagination_token is None:
        print(Fore.GREEN + "INFO: End of Cognito User Pool reached")

    time.sleep(0.15)

json.dump(all_users, json_file, indent=4, default=datetimeconverter)
json_file.close()
