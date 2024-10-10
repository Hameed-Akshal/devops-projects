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

#### 1. In the Lambda function's **Code** section, replace the default handler with the provided Python code from main.py .Click **Deploy** to save the changes.
