<!--StartFragment-->

# **Update ami patch using lambda and cloudwatch events.**


### **Step 1: Create IAM Policy for Lambda Execution**

####  **1.1: Navigate to IAM Console**

1. Go to the IAM (Identity and Access Management) section in the AWS Management Console.
2. On the left sidebar, click on Policies.


#### **1.2: Create a New Policy**

1. Click the Create policy button.
2. Switch to the JSON tab.


#### **1.3: Define the Policy**

1. Paste the following policy JSON, ensuring that you are replacing accountid with your AWS account ID and  resource ARNs  with specific values as needed:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DeregisterImage",
                "ec2:DescribeLaunchTemplateVersions",
                "ec2:CreateLaunchTemplateVersion",
                "ec2:ModifyLaunchTemplate",
                "ec2:DescribeSubnets",
                "ssm:StartAutomationExecution",
                "ssm:DescribeAutomationExecutions",
                "ssm:GetAutomationExecution"
            ],
            "Resource": [
                "arn:aws:ec2:us-east-2:accountid:image/*",                  
                "arn:aws:ec2:us-east-2:accountid:launch-template/*",         
                "arn:aws:ec2:us-east-2:accountid:subnet/*",                 
                "arn:aws:ssm:us-east-2:accountid:automation:*"               
            ]
        },
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:us-east-2:accountid:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
               "arn:aws:logs:us-east-2:accountid:log-group:/aws/lambda/amipatch:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::accountid:role/AutomationServiceRole"
        }
    ]
}
```
2. Click **Review policy**.

3. Provide a name for the policy, such as `LambdaAmiPatchPolicy`, and add an optional description.

4. Click **Create policy**.

### **Step 2: Create IAM Role for Lambda Execution**

#### **2.1: Navigate to Roles**

1. In the IAM console, click on **Roles** in the left sidebar.


#### **2.2: Create a New Role**

1. Click the **Create role** button.

2. Under **Trusted entity type**, select **Lambda**.

3. Click **Next** to attach permissions.


#### **2.3: Attach Necessary Policies**

1. In the **Attach permissions policies** section, search for the **AWSLambdaBasicExecutionRole** policy and select it. This policy allows Lambda functions to write logs to Amazon CloudWatch.

2. Click **Next**.


#### **2.4: Complete Role Creation**

1. Review the permissions, then click **Next**.

2. Provide a name for the role, such as `LambdaAmipatchRole`.

3. Review your settings, then click **Create role**.


### **Step 3: Attach the Custom Policy to the Role**

#### **3.1: Attach Policy**

1. In the IAM console, go back to the **Roles** section.

2. Find and click on the role you just created (`LambdaAmipatchRole`).

3. Click on the **Permissions** tab.

4. Click **Add permissions** and select **Attach policies**.

5. Search for the policy you created (`LambdaAmiPatchPolicy`), select it, and click **Attach policy**.

### **Step 4: Create IAM Role for AMI Patch**

#### **4.1: Navigate to IAM Roles**

1. In the IAM console, click on **Roles** in the left sidebar.


#### **4.2: Create a New Role**

1. Click the **Create role** button.

2. Under **Trusted entity type**, select **AWS service**.

3. Choose **EC2** from the list of services (since the role is for instances).

4. Select **Next: Permissions**.


#### **4.3: Attach Necessary Policies**

1. In the **Attach permissions policies** section, search for `AmazonSSMManagedInstanceCore` and select it.

2. Click **Next: Tags** (you can skip adding tags).

3. Click **Next: Review**.


#### **4.4: Complete Role Creation**

1. Provide a name for the role, such as `ami-patch-role`.

2. Review your settings, then click **Create role**.


### **Step 5: Create IAM Role for Automation Service**

#### **5.1: Navigate to Roles**

1. In the IAM console, click on **Roles** in the left sidebar.


#### **5.2: Create a New Role**

1. Click the **Create role** button.

2. Under **Trusted entity type**, select **AWS service**.

3. Choose **Systems Manager** from the list of services.

4. Select **Next: Permissions**.


#### **5.3: Attach Necessary Policies**

1. In the **Attach permissions policies** section, search for `AmazonSSMAutomationRole` and select it.

2. Click **Next: Tags** (you can skip adding tags).

3. Click **Next: Review**.


#### **5.4: Complete Role Creation**

1. Provide a name for the role, such as `AutomationServiceRole`.

2. Review your settings, then click **Create role**.


### **Step 6: Create Inline Policy for Automation Service Role**

#### **6.1: Attach Inline Policy**

1. In the IAM console, go to the **Roles** section and find the `AutomationServiceRole`.

2. Click on the role to open its details.

3. Click on the **Permissions** tab.

4. Click on **Add inline policy**.


#### **6.2: Define the Inline Policy**

Switch to the **JSON** tab and paste the following policy JSON, replacing `accountid` with your AWS account ID:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::accountid:role/ami-patch-role"
        }
    ]
}
```
#### **6.3: Review and Create Policy**

1. Click **Review policy**.

2. Provide a name for the inline policy, such as `PassAmiPatchRolePolicy`.

3. Click **Create policy**.

<!--StartFragment-->


### **Step 7: Update Trust Relationship for Automation Service Role**

#### **7.1: Navigate to IAM Roles**

1. In the IAM console, go to the **Roles** section.

2. Find and click on the `AutomationServiceRole` that you created earlier.


#### **7.2: Edit Trust Relationships**

1. Click on the **Trust relationships** tab.

2. Click on the **Edit trust relationship** button.


#### **7.3: Update the Trust Policy**

<!--EndFragment-->

1. Replace the existing trust policy with the following JSON, ensuring to replacing `accountid` with your AWS account ID:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ssm.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "accountid"
                },
                "ArnLike": {
                    "aws:SourceArn": "arn:aws:ssm:*:accountid:automation-execution/*"
                }
            }
        }
    ]
}
```
#### **7.4: Review and Save Changes**

#### <!--StartFragment-->1) Click **Update Trust Policy** to save the changes.

### **Step 8: Create the Lambda Function**

#### 1. Navigate to the **Lambda** console.

2. Click **Create function**.

   - **Function name**: `ami-patch`

   - **Runtime**: Python 3.x (select the appropriate version, like Python 3.9)

   - **Execution role**: Select **Use an existing role** and choose the `LambdaAmiPatchRole` created in Step 1.

3. Click **Create function**.

### **Step 9: Add the Lambda Function Code**

#### 1. In the Lambda function's **Code** section, replace the default handler with the provided Python code from main.py 

#### 2. Click **Deploy** to save the changes.

### **Step 10: Configure the Lambda Function**

1. **Environment Variables**: Add any necessary environment variables, such as the `launch_template_id` (if you prefer not to hard-code it).

2. **Timeout**: Increase the function timeout to allow sufficient time for automation execution (e.g., 15 minutes).

3. **Memory**: Set an appropriate memory limit (e.g., 512 MB).


### **Step 11: Test and Verify the Lambda Function Output**

After deploying the Lambda function code, you can create a test event and verify the output.

1. **Create a Test Event**:

   - Go to the **Test** tab in the AWS Lambda console.

   - Create a new test event and name it `amipatch` (or any name of your choice).

   - You can leave the event body empty or use a simple event structure such as: `{}`

2. **Run the Test**:

   - After creating the test event, click **Test** to execute the Lambda function.


3. **Expected Response**: After the function completes, you should see the following output in the **Response** section:
```
{\
  "statusCode": 200,\
  "body": "{\\"message\\": \\"Launch template updated successfully.\\", \\"NewAmiId\\": \\"ami-09d416d4184a51382\\", \\"LaunchTemplateVersion\\": 3}"\
}
```

<!--StartFragment-->

4. **Function Logs**: The **Function Logs** will contain details about the execution. An example log output is as follows:\
   \
   `START RequestId: dc27c6ae-66fc-426d-be71-924c59635ae2 Version: $LATEST`

<!---->

    Current AMI ID from Launch Template lt-0b532fbadaa7a4935: ami-05867a0641dc03966
    ami-05867a0641dc03966
    Using Subnet ID: subnet-050631224345caa2a
    Found Subnet ID: subnet-050631224345caa2a
    Started SSM Automation with Execution ID: d048d3e3-28d3-4ce3-9995-c31f7b66e1ca
    Automation Execution Status: InProgress
    Waiting for automation to complete...
    Automation Execution Status: Success
    SSM Automation Outputs: {"createImage.ImageId": ["ami-09d416d4184a51382"]}
    New AMI ID: ami-09d416d4184a51382
    Launch template updated with new AMI ID: ami-09d416d4184a51382
    Launch template version 3 set as the default.
    END RequestId: dc27c6ae-66fc-426d-be71-924c59635ae2
    REPORT RequestId: dc27c6ae-66fc-426d-be71-924c59635ae2	Duration: 373322.10 ms	Billed Duration: 373323 ms	Memory Size: 128 MB	Max Memory Used: 93 MB	Init Duration: 306.54 ms

5. Key log entries:

   - **Current AMI ID**: The AMI currently in use by the launch template.

   - **Subnet ID**: The subnet used for the patch process.

   - **Started SSM Automation**: The automation execution ID to track the AMI patching process.

   - **Automation Execution Status**: Progress updates on the patching process (e.g., `InProgress`, `Success`).

   - **New AMI ID**: The ID of the newly created AMI after the update.

   - **Launch template updated**: The confirmation that the launch template has been updated with the new AMI.

   - **Launch template version set**: Confirmation that the new launch template version has been set as the default.

   - **Request ID**: The unique ID for tracking the request (e.g., `dc27c6ae-66fc-426d-be71-924c59635ae2`). You can use this ID to locate specific logs in CloudWatch.

**Step 11: Create IAM Role for CloudWatch Events**

1. **Go to the IAM Console**:

   - Navigate to the IAM Console.

2. **Create a New Role**:

   - Click on **Roles** in the left sidebar, and then click **Create role**.

3. **Select Trusted Entity**:

   - Under **Trusted entity type**, select **AWS service**.

   - In the **Use cases for other AWS services**, select **EventBridge (CloudWatch Events)** and then click **Next**.

4. **Attach Policies**:

   - In the **Attach permissions policies** section, search for and select the following policy:

     - **AWSLambdaRole**: This policy allows CloudWatch Events to invoke Lambda functions.

   - Click **Next**.

5. **Role Name and Tags**:

   - In the **Role name** field, enter a name for your role (e.g., `EventBridge-Lambda-Invoke-Role`).

   - Optionally, add tags if you want to associate metadata with the role.

   - Click **Create role**.


### **Step 12: Add Policy to Allow Lambda Invocation**

1. **Go to the IAM Console**:

   - Navigate to the[ IAM Console](https://console.aws.amazon.com/iam/).

2. **Find the Role**:

   - In the left sidebar, click **Roles**.

   - Search for the role you created (e.g., `EventBridge-Lambda-Invoke-Role`).

3. **Attach Inline Policy**:

   - Under the role details, click on the **Permissions** tab.

   - Scroll down and click **Add inline policy**.

   - In the JSON editor, paste the following policy to allow invocation of the `amipatch` Lambda function:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:us-east-2:account-id:function:amipatch"
      ]
    }
  ]
}
```

4. **Review and Add**:

   - After pasting the policy, click **Review policy**.

   - Give the policy a name (e.g., `InvokeLambdaFunctionPolicy`) and click **Create policy**.


### **Step 13: Update Trust Relationships**

1. **Go to the Trust Relationships Tab**:

   - In the role details for `EventBridge-Lambda-Invoke-Role`, click on the **Trust relationships** tab.

   - Click **Edit trust relationship**.

2. **Edit the Trust Relationship**:

   - Replace the existing trust relationship JSON with the following:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

3. **Save Changes**:

   - After updating the JSON, click **Update trust policy**.

\



### **Step 14: Create a CloudWatch Events Rule**

1. **Open the Amazon EventBridge Console**:

   - Navigate to the[ Amazon EventBridge Console](https://console.aws.amazon.com/events/).

2. **Create a Rule**:

   - In the EventBridge console, click **Create rule**.

   - Enter a **Name** for your rule (e.g., `every-two-weeks-ami-patch`).

   - Optionally, add a **Description**.

3. **Define the Schedule**:

   - Under **Define pattern**, choose **Event Source**: `EventBridge (CloudWatch Events)`.

   - Under **Event Source**, choose **Schedule**.

   - Select **Rate expression** and enter the value `rate(14 days)` to trigger the Lambda every 14 days.

     - Example: `rate(14 days)`

4. **Target**:

   - In the **Select targets** section, choose **Lambda function** as the target.

   - In the **Function** dropdown, select your Lambda function (e.g., `ami-patch`).

5.  **Choose an Existing IAM Role:**

- **In the Execution role section, select the IAM role you created earlier (e.g.,** `EventBridge-Lambda-Invoke-Role`**).**

6. **Review and Create**:

   - Review your rule configuration, and then click **Create rule**.

<!--EndFragment-->

<!--EndFragment-->


