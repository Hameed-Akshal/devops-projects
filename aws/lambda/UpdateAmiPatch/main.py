import boto3
import json
import time
from datetime import datetime

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format string
        return super(DateTimeEncoder, self).default(obj)

# Fetch the AMI ID from the launch template
def fetch_ami_from_launch_template(launch_template_id):
    ec2_client = boto3.client('ec2')
    
    try:
        response = ec2_client.describe_launch_template_versions(
            LaunchTemplateId=launch_template_id,
            Versions=['$Latest']
        )
        launch_template_version = response['LaunchTemplateVersions'][0]
        ami_id = launch_template_version['LaunchTemplateData']['ImageId']
        print(f"Current AMI ID from Launch Template {launch_template_id}: {ami_id}")
        return ami_id
    
    except Exception as e:
        print(f"Error fetching AMI from Launch Template: {str(e)}")
        return None

# Fetch any available subnet in the account
def fetch_any_subnet():
    ec2_client = boto3.client('ec2')
    try:
        # Fetch subnets without filtering for default subnets
        response = ec2_client.describe_subnets()

        # Check if there are any subnets available
        if response['Subnets']:
            subnet_id = response['Subnets'][0]['SubnetId']
            print(f"Using Subnet ID: {subnet_id}")
            return subnet_id
        else:
            print("No subnets found.")
            return None

    except Exception as e:
        print(f"Error fetching subnet: {str(e)}")
        return None

# Start SSM Automation execution
def start_ssm_automation(latest_ami_id, subnet_id):
    ssm_client = boto3.client('ssm')
    params = {
        'SourceAmiId': [latest_ami_id],
        'AutomationAssumeRole': ['arn:aws:iam::accountid:role/AutomationServiceRole'],
        'IamInstanceProfileName': ['ami-patch-role'],  # Modify as needed
        'InstanceType': ['t3.micro'],  # Instance type for the patch process
        'IncludePackages': ['all'],  # Packages to include in the update
        'ExcludePackages': ['none'],  # Packages to exclude
        'MetadataOptions': ['{"HttpEndpoint":"enabled","HttpTokens":"optional"}'],  # Metadata options
        'SubnetId': [subnet_id],  # Add the subnet ID
        'PostUpdateScript': ['none'],  # No post-update script
        'PreUpdateScript': ['none']  # No pre-update script
    }
    
    try:
        response = ssm_client.start_automation_execution(
            DocumentName='AWS-UpdateLinuxAmi',  # Replace with your automation document
            Parameters=params
        )
        automation_execution_id = response['AutomationExecutionId']
        print(f"Started SSM Automation with Execution ID: {automation_execution_id}")
        return automation_execution_id
    except Exception as e:
        print(f"Error starting SSM automation: {str(e)}")
        return None
    

# Check SSM automation status.
def check_automation_status(automation_execution_id):
    ssm_client = boto3.client('ssm')
    
    while True:
        try:
            response = ssm_client.get_automation_execution(
                AutomationExecutionId=automation_execution_id
            )
            status = response['AutomationExecution']['AutomationExecutionStatus']
            print(f"Automation Execution Status: {status}")
            
            if status == 'Success':
                return response
            elif status in ['Failed', 'TimedOut', 'Cancelled']:
                print(f"Automation failed with status: {status}")
                return None
            else:
                print("Waiting for automation to complete...")
                time.sleep(30)
                
        except Exception as e:
            print(f"Error checking automation status: {str(e)}")
            return None
            

# Function to update the launch template with the new AMI ID
def update_launch_template_with_new_ami(launch_template_id, new_ami_id):
    
    ec2_client = boto3.client('ec2')
    try:
        # Fetch the current version of the launch template
        response = ec2_client.describe_launch_template_versions(
            LaunchTemplateId=launch_template_id,
            Versions=["$Latest"]
        )
        
        latest_version = response['LaunchTemplateVersions'][0]
        
        # Update the launch template with the new AMI ID
        updated_template = ec2_client.create_launch_template_version(
            LaunchTemplateId=launch_template_id,
            SourceVersion=str(latest_version['VersionNumber']),
            LaunchTemplateData={
                'ImageId': new_ami_id
            }
        )
        
        print(f"Launch template updated with new AMI ID: {new_ami_id}")
        
        new_version_number = updated_template['LaunchTemplateVersion']['VersionNumber']
        print(f"Launch template updated with new AMI ID: {new_ami_id}, New Version: {new_version_number}")
        
        # Set the newly created version as the default version
        ec2_client.modify_launch_template(
            LaunchTemplateId=launch_template_id,
            DefaultVersion=str(new_version_number)
        )
        
        print(f"Launch template version {new_version_number} set as the default.")
        
        return updated_template
    except Exception as e:
        print(f"Failed to update launch template: {e}")
        return None




# Main Lambda handler
def lambda_handler(event, context):
    launch_template_id = 'lt-0b532fbw2737a4935'  # Replace with your template ID
    
    # Step 1: Fetch the current AMI from the launch template
    latest_ami_id = fetch_ami_from_launch_template(launch_template_id)
    
    if not latest_ami_id:
        return {
            'statusCode': 404,
            'body': json.dumps("No AMI found.")
        }
    else:
        print (latest_ami_id)


    # Step 2: Fetch the default subnet ID
    subnet_id = fetch_any_subnet()

    if subnet_id:
        print(f"Found Subnet ID: {subnet_id}")
    else:
        print("Could not find any subnet.")
    
    # Step 3: Start SSM automation to patch/update the AMI
    automation_execution_id = start_ssm_automation(latest_ami_id, subnet_id)
    
    if not automation_execution_id:
        return {
            'statusCode': 500,
            'body': json.dumps("Failed to start SSM Automation.")
        }
    else:
        print(f"Started SSM Automation with Execution ID: {automation_execution_id}")
        
    # Step 4: Check SSM automation status
    automation_result = check_automation_status(automation_execution_id)
    
    if not automation_result:
        return {
            'statusCode': 500,
            'body': json.dumps("SSM Automation failed.")
        } 
        
    # Step 5: Fetch the newly created AMI details after successful execution
    outputs = automation_result['AutomationExecution'].get('Outputs', {})
    
    # Log the outputs to inspect the actual structure
    print(f"SSM Automation Outputs: {json.dumps(outputs)}")
    
    new_ami_id = outputs.get('createImage.ImageId', [None])[0]
    print (f"my last output  {new_ami_id}")
    
    if new_ami_id:
        print(f"New AMI ID: {new_ami_id}")
        
        # Step 4: Update the launch template with the new AMI ID
        updated_template = update_launch_template_with_new_ami(launch_template_id, new_ami_id)
        
        if updated_template:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Launch template updated successfully.',
                    'NewAmiId': new_ami_id,
                    'LaunchTemplateVersion': updated_template['LaunchTemplateVersion']['VersionNumber']
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps("Failed to update the launch template.")
            }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps("Failed to retrieve new AMI details.")
        }
