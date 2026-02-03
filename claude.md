AI agents can act as autonomous workers to solve complex problems. Now, you get to build a team of them.

The Scenario: A Digital Banking Revolution
Imagine you work for a large international bank. Every single day, thousands of financial messages called SWIFT messages fly between your bank and others around the globe. These messages are the backbone of international money transfers, containing instructions to move millions of dollars. The challenge is that this process needs to be fast, accurate, and secure. Every message with an error has to be manually corrected by a human, which costs the bank time and money. Even worse, some of these transactions might be fraudulent. How can a bank possibly keep up?

This is where your AI system comes in.

Your Mission: Build an Agentic SWIFT Processing System
What is SWIFT? Think of it as the messaging system for the global banking world. When banks send money to each other across borders, they send a SWIFT message. It’s a secure, standardized way to communicate financial transactions. As you can guess, making sure these transactions are legitimate is a top priority for any bank.

In this project, you will build a multi-agent system to automate the processing of a batch of SWIFT transactions. Your system will be responsible for:

Validating and Correcting incoming messages to make sure they meet SWIFT standards.
Detecting Potential Fraud by analyzing transaction patterns.
Processing Clean Transactions efficiently.
You won't be building just one AI; you'll be implementing a pipeline of specialized agents that work together, each based on a specific agentic workflow design pattern.

Meet Your Team of Agents:

The Evaluator-Optimizer Agent: Think of this as your Quality Control Specialist. Its job is to inspect every incoming SWIFT message, identify any errors, and intelligently correct them.
The Parallelization Agent: This is your Dispatcher. To work faster, it will take the batch of validated messages and distribute them among multiple workers for simultaneous fraud screening.
The Prompt Chaining Agent: This is the Lead Fraud Investigator. For transactions that look suspicious, this agent performs a deeper, multi-step analysis to gather more evidence before making a final judgment.
The Orchestrator-Worker Agent: This is the Operations Manager. It takes the clean, verified transactions and delegates the final processing tasks to worker agents.
Banks measure their efficiency using a metric called the Straight-Through Processing (STP) rate—the percentage of transactions processed with zero manual intervention. A high STP rate saves millions of dollars. By building this system, you'll learn how AI agents can directly impact a financial institution's bottom line by improving efficiency and reducing risk.


You'll build a system of AI agents that collaborate to process and analyze SWIFT messages. You will implement four distinct agent patterns:

The Evaluator-Optimizer: This agent acts as a quality checker. It first evaluates each SWIFT message to see if it's formatted correctly and then optimizes it by fixing any errors it finds.
The Parallelization Agent: To work efficiently, this agent processes many messages at once. You'll create multiple fraud detection agents that run in parallel to check for different types of suspicious patterns.
The Prompt Chaining Agent: This is like a detective squad. One agent does an initial screening, then passes its findings to a technical expert, who passes it to a risk assessor, and so on. Each agent adds to the analysis in a conversational chain.
The Orchestrator-Worker: This is our project manager. The orchestrator agent looks at the big picture—all the "clean" transactions—and breaks down the final processing into logical tasks for a team of worker agents to execute.
You're given a starter code repository that has all the starter code you'll need, like data models and services, already built for you. Your job is to implement the core logic for each of the four agent patterns. You will follow the TODO comments in the code, which will guide you through each step of building this powerful fraud detection system.

Download the starter files from the workspace on the following page

Guide to starter code
/models directory : The swift_message.py, bank.py, and transaction.py files. You'll need these data structures to work with.

/services/: The swift_generator.py and llm_service.py files. The logic for generating fake SWIFT data and interacting with the OpenAI API.

config.py: The project configuration.
generate_swift_messages.py: The script to create sample data files.
pyproject.toml: The file that lists project dependencies.
Files with "TODO" Items for You to Complete:

main.py: The main application entry point. Call the different agent patterns in the correct sequence.
/agents/workflow_agents/base_agents.py: Create a base agent class and correctly define how agents interact with the LLM service.
/agents/parallelization.py: Implement the logic to process messages concurrently and add a new fraud detection agent.
/agents/prompt_chaining.py: Complete the conversation chain by implementing the steps for the Technical Analyst and Compliance Officer.
/agents/orchestrator_worker.py: Implement the orchestrator that breaks down the main goal into subtasks for worker agents.


Project Instructions
Step 1: Get Familiar with the Project
Your goal is to build a system that can:

Read a batch of SWIFT messages from a file.
Clean and validate each message.
Analyze the messages for potential fraud using multiple specialized agents.
Organize the final, validated transactions into a structured report.
Familiarize yourself with the project structure. The main logic is in the agents/ directory, and the main.py file is where the entire workflow is executed.

Step 2: Generate Your Data
Before you can process any data, you need to create some. The project includes a script for this purpose.

Open the terminal in your VS Code workspace.
Run the following command:
python generate_swift_messages.py
This will create a swift_messages.csv file inside the /data directory. This file contains the raw SWIFT messages your agents will work with. Some of these messages intentionally have errors, and some might be fraudulent—it's your system's job to figure that out.
Step 3: Implement the Evaluator-Optimizer Agent
The Concept: This first agent acts as a quality control specialist. It follows a two-step pattern:

Evaluate: It first checks a SWIFT message against a set of rules (a "golden prompt") to see if it's valid.
Optimize: If the message is invalid, the agent's goal is to fix it.
Your Task:

Navigate to the agents/ directory and open the evaluator_optimizer.py file.
Inside the EvaluatorOptimizerAgent class, you will find a TODO.
Your task is to implement the logic that first calls the evaluator_agent to check the message.
Then, based on the evaluator's feedback, you will either approve the message as-is or pass it to the optimizer_agent to be corrected.
The method should return the final, validated SWIFT message.
Step 4: Implement the Parallelization Agent
The Concept: Processing messages one by one can be slow. To speed things up, we can use multiple agents working in parallel, with each agent assigned a specific fraud detection task.

Your Task:

Open the agents/parallelization.py file.
Your first TODO is to complete the run_agents_in_parallel function. You will need to use Python's concurrent.futures.ThreadPoolExecutor to run a list of fraud-detection agents simultaneously on each SWIFT message.
Your second TODO is to create a new, simple fraud detection agent. Define a new prompt that describes a specific fraudulent pattern (for example, "transactions to a high-risk country"). Then, add this new agent to the list of agents that will be run in parallel.
Step 5: Implement the Prompt Chaining Agent
The Concept: Sometimes, a complex analysis requires multiple perspectives. A prompt chaining agent works like an assembly line. The output of one agent becomes the input for the next, creating a chain of analysis. In our case, a Junior Analyst does an initial check, a Technical Analyst reviews the details, and a Compliance Officer gives the final sign-off.

Your Task:

Open the agents/prompt_chaining.py file.
Inside the PromptChainingAgent class, you will find a TODO.
Your task is to complete the conversation chain. You will need to:
Take the initial analysis from the Junior Analyst.
Pass it to the Technical Analyst for a more detailed review.
Pass the combined analysis to the Compliance Officer for the final decision.
The method should return the complete conversation history.
Step 6: Implement the Orchestrator-Worker Pattern
The Concept: For the final step, an Orchestrator agent acts as the project manager. It takes the list of all the cleaned and approved transactions and decides how to best organize them. It then gives instructions to Worker agents to perform the actual formatting.

Your Task:

Open the agents/orchestrator_worker.py file.
Inside the OrchestratorWorker class, you will find a TODO.
Your task is to implement the logic for the orchestrator.
First, the orchestrator_agent will analyze the list of transactions and propose a plan for how to group them (for example, by bank or by currency).
Next, you will call the worker_agent, providing it with both the orchestrator's plan and the list of transactions. The worker will then execute the plan and return the final, structured report.
Step 7: Run the Full System
Once you have completed all the TODO items, it's time to see your multi-agent system in action.

Open the main.py file.
Review the file to see how all the agents you built are called in sequence.
In your terminal, run the main script:
python main.py
Watch the output in the terminal. You should see the logs from each agent as it processes the messages, detects fraud, and organizes the final output. Congratulations, you've now built a sophisticated, multi-agent system for financial message processing!