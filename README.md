# TAL Chatbot Setup and Installation Guide

# Semantic Kernel Chatbot

## Azure Setup

**Step 1: Create an Azure Account**

**Prerequisites -** 

Before you begin, you'll need:

- A valid email address (Microsoft account or GitHub account)
- A phone number for verification
- A credit card or debit card (non-prepaid) for identity verification[1](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)

**Account Creation Process**

1. **Navigate to Azure Website**
    - Go to [the azure sign up page](https://signup.azure.com/)
2. **Sign In or Create Microsoft Account**
    - Sign in with an existing Microsoft account or create a new one
    - You can also use the "Sign in with GitHub" option if you prefer
    - Enter all the required details
3. **Identity Verification**
    - Microsoft will send a numeric OTP to your registered email and phone number
    - Enter the OTP on the Azure account creation page to complete verification
4. **Choose Subscription Type**
    - Select the **Azure Pay as you go** option, which includes:
        
        For more information on subscriptions and get-started guides, visit [azure pricing information](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account#azure-video-123) page.
        
5. **Payment Information**
    - Provide credit card details for identity verification (no charges will be made for free accounts)
    - You may see a temporary $1 verification hold that will be removed
6. **Review and Accept Terms**
    - Review the Azure terms of service and privacy policy
    - Click **"Create"** to complete your Azure account setup

---

**Step 2: Access the Azure Portal**

1. **Login to Azure Portal**
    - Navigate to [**`portal.azure.com`**](https://portal.azure.com/)
    - Sign in using your Microsoft credentials
2. **Familiarize Yourself with the Interface**
    - The Azure portal provides access to all Azure services and resources
    - You'll use this interface for all subsequent steps

## Cosmos DB Storage Setup

**Step 1: Create a Resource Group**

A Resource Group is a container that holds related resources for an Azure solution, making them easier to manage and monitor.

---

**Step 2: Creating the Resource Group**

1. **Navigate to Resource Creation**
    - From the Azure portal menu or Home page, select **"Create a resource"**
    - In the search bar, type "Resource Group" and select it from the results
2. **Configure Resource Group Settings**
    - Click **"Create"** to start the resource group creation process
    - Fill in the following details:
        - **Resource Group Name**: Choose a unique, descriptive name (e.g., "RG-TAL-Chatbot")
        - **Subscription**: Select your active Azure subscription
        - **Region**: Locate and select `Sweden Central` as it the only location that supports hosting OpenAI GPT models on Azure Foundry which we will later deploy.
3. **Review and Create**
    - Click **"Review + create"** to validate your setting
    - Once validation passes, click **"Create"** to deploy the resource group
4. **Confirmation**
    - Wait for the "Resource group created" notification
    - You can pin the resource group to your dashboard for easy access

---

**Step 3: Create Azure Cosmos DB Account**

**Initiating Cosmos DB Creation**

1. **Start Resource Creation**
    - From the Azure portal menu or Home page, select **"Create a resource"**
    - Search for "Azure Cosmos DB" in the marketplace
    - Select **"Create" > "Azure Cosmos DB"**
2. **Choose API Type**
    - On the "Create an Azure Cosmos DB account" page, select the **"Create"** option within the **"Azure Cosmos DB for NoSQL"** section

**Configure Cosmos DB Account Settings**

1. **Basic Configuration**
    
    Fill in the following essential settings on the **Basics** tab
    
    | **Setting** | **Value** | **Description** |
    | --- | --- | --- |
    | **Subscription** | Your subscription name | Select the Azure subscription for this account |
    | **Resource Group** | Previously created group | Select the resource group you created in Step 3 |
    | **Account Name** | Unique global name | Enter a globally unique name (3-44 characters, lowercase letters, numbers, and hyphens only) |
    | **Location** | Closest region | Choose `Sweden Central` again for consistency |
    | **Capacity Mode** | Provisioned throughput or Serverless | Choose based on your workload requirements 
    For the simple prototype, we used Serverless. |
    | **Apply Free Tier Discount** | Apply or Do not apply | Apply this as the data stored in CosmosDB does not cross the free limit. |
2. **Advanced Settings (Optional)**
    - Configure encryption, backup policy, redundancy, and multi-region writes as needed
    - Set up throughput limits to prevent unexpected charges
3. **Review and Deploy**
    - Click **"Review + Create"** to validate your configuration
    - Review all settings carefully
    - Click **"Create"** to deploy your Cosmos DB account
    - Deployment typically takes 5-10 minutes to complete

---

**Step 4: Create Database and Container**

Once your Cosmos DB account is deployed, you'll need to create a database and container to store your data.

We will do this via the python script provided in the source code at `./SemanticKernelChatbot/CosmosDBHandlers/cosmosConverterUploader.py`

Before this, we need to install some required packages.

- Create a virtual environment (either .venv. or .conda) in your code editor for the folder the source code is in (I’m using VSCode). This is not needed but is considered good practice.
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image.png)
    
- After creating the virtual environment using python 3.11, make sure it is activated in the terminal. You should see a prefix like (.conda) or (.venv) before your directory path.
- Now, run pip install -r `./SemanticKernelChatbot/requirements.txt` from the root path of the source code.
- This should successfully install all the required packages.

To use this script we will need to get some access keys from the portal.

- First, we need to create a `.env` file in the `./SemanticKernelChatbot` directory.
- Navigate to the Keys section in the menu bar on the left.
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%201.png)
    
    - Copy the URI shown at the top and and store it as `AZURE_COSMOS_DB_ENDPOINT = <copied_uri>`  in the .env file.
    - Copy the PRIMARY KEY and store it as `AZURE_COSMOS_DB_KEY = <copied_key>`  in the .env file as well.

We can now run the `./cosmosConverterUploader.py` to upload the converters from the `.json` file into Cosmos DB. If successful, the script will print a success message along with the number of converters uploaded for you to verify. 

You should also see the newly created database and container in the Data Explorer section.

![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%202.png)

**Explore Additional Features**

- Review multi-region replication options if needed
- Configure backup and security settings as required
- Set up monitoring and alerts for your Cosmos DB account

## Deploy required AI models on Azure Foundry

**Step 1: Open Azure AI Foundry Portal**

- Navigate to [`ai.azure.com`](https://ai.azure.com/)
- Sign In again if necessary.

---

**Step 2: Create a Project**

- Click on **Create New** at the top right corner of the screen
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%203.png)
    
- Select the “**Azure AI Foundry Resource Type → Next”** when prompted
- Enter a new project name of your choice and a resource name. Ensure that the Resource Group is the same one we created and used for the Cosmos DB account and that the region is set to Sweden Central. Then click “Next”.
- This should take about 5-10 minutes.
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%204.png)
    

---

**Step 3: Deploy GPT Model**

- Navigate to “My Models and Endpoints” using the menu on the left.
- Click on “Deploy Model > Deploy base model”
- Search for a gpt model of your choice using the search bar or a newer/smarter version based on your preference. Check pricing in the Overview page before doing so. We chose GPT-4o-mini as it offers a decent performance at low price but it will soon be deprecated. (gpt-4.1-mini might be a good alternative)
- Let the default options be. If you wish, you can change the deployment name and the token limit.

---

**Step 4: Get the Keys to access this model from a script**

- Select the gpt model deployment just created
- Copy the **Target URI** and save it as `AZURE_OPENAI_ENDPOINT=<copied_uri>` in the same .env file as earlier.
- Similarly, copy the **Key** under the URI and save it as `AZURE_OPENAI_KEY=<copied_key>` .
- Also save these variables. You should find the api version here
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%205.png)
    
    ```xml
    OPENAI_API_TYPE = azure
    AZURE_OPENAI_API_VERSION = <api_version>
    AZURE_OPENAI_DEPLOYMENT_NAME = <your_deployment_name>
    ```
    

---

**Step 5: Deploying and getting the keys for a Text Embeddings Model**

- This is not necessary for the chatbot but will be used for chat logging and analytics purposes later on.
- Deploy a text-embedding-ada model of your choice in a process similar to the gpt model deployment. We used a text-embedding-ada-002 model.
- Now navigate to the Overview page and copy the Azure AI Endpoint and save it as `OPENAI_API_ENDPOINT=<copied_endpoint>` in the same .env file. Also save the the name of your text embedding model deployment as `OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT=<deployment_name>.`
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%206.png)
    

## Run the Chatbot

- Simply run the `chatbot-gradio.py` script in the `SemanticKernelChatbot` folder.
- If there aren’t any issues, you should see the following output
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%207.png)
    
    - `Ctrl/Cmd + Click` on the URL shown and it will direct you to the locally deployed chatbot!
    
    ![image.png](Installation%20Guide%20215825add12a80c3853fe4e47925072f/image%208.png)
    
    **Chat History Support**
    
    - If in the future, if you’d like to add support for chat history so that the AI is capable of understanding context from previous questions, you can try running the demo in the [`chatbot-gradio-chatHistory.py`](http://chatbot-gradio-chatHistory.py) file.
    - Keep in mind, the demo is set to store only 4 messages in. history per session, after which it refreshes. This is to prevent rising token usage per new question and processing time.

---

# Ollama + LangChain Chatbot

## Setup Required Tokens

Get Hugging Face API Token

1. Create a Hugging Face Account
2. Go to [https://huggingface.co](https://huggingface.co/)
3. Click Sign up (top-right corner) or Log in if you already have an account.
4. Access Your Settings
5. Once logged in, click your profile picture (top-right)
6. Choose "Settings" from the dropdown
7. Go to Access Tokens
8. In the left sidebar, click on "Access Tokens"
URL: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
9. Create a New Token
10. Click the "New token" button and give it a name like tal-bot.
11. Set the Role to: Read
12. Click "Generate token" and copy the generated token immediately. It will not be shown again.
13. Save the Token in Your .env File
    - Create a `.env` file in the `./ChatbotHugg` folder: `HUGGINGFACEHUB_API_TOKEN=<your_token_here>`.
    - Replace your_token_here with the one you copied.
14. Restart Your Python Script
    - Make sure your script includes this:
        
        ```python
        from dotenv import load_dotenv
        load_dotenv()
        ```
        
    - This loads the token from .env so it can be used automatically by Hugging Face components like: HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2").

## Run the Chatbot

1. **System Requirements**
    - OS: macOS / Linux (Ollama is not yet natively supported on Windows without WSL)
    - Python: 3.9–3.11 recommended
    - Disk space: ~10GB free (for Ollama + model)
    - RAM: At least 8GB (16GB+ recommended)
2. **Install Ollama and LLaMA 3 Model**
3. **Install Ollama**
    - Follow instructions for your OS from: [https://ollama.com/download](https://ollama.com/download)
    - Pull the LLaMA 3 model with your system prompt customization
    - If you have your own Modelfile (as implied by FROM llama3), create a folder and save this as Modelfile:
        
        ```docker
        FROM llama3
        SYSTEM """
        You are an expert assistant for TAL LED converters.
        ALWAYS follow these rules:
        1. Use ONLY the provided JSON technical data to answer
        2. Never invent specifications
        3. If unsure, say "I don't know"
        4. Format responses clearly with markdown tables
        5. Cite ARTNRs from the data
        ```
        
4. **Build the model**
    
    ```docker
    ollama create tal-converter-bot -f ./Modelfile
    ```
    
5. **Set Up Python Environment**
Create and activate a virtual environment 
    
    ```bash
    python -m venv talenv
    source talenv/bin/activate  # macOS/Linux
    ```
    
6. **Install required Python packages**
    - You can create a requirements.txt file:
        
        ```bash
        gradio
        ollama
        langchain
        langchain-community
        langchain-core
        langchain-huggingface
        sentence-transformers
        python-dotenv
        ```
        
    - Then run: `pip install -r requirements.txt`
7. **Prepare Your Data**
Ensure the JSON file is located at: `TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json`
8. **Run the Chatbot Script**
Run the `tal_chatbot.py` script. You can run: `python ./tal_chatbot.py`

---
