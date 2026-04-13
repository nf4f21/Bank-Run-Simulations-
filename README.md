🏦 Bank Run Simulation

A computational simulation project exploring the causes and dynamics of bank runs and financial instability.
This repository contains the code and experiments created for my final-year dissertation.

📌 Overview

A bank run occurs when many depositors withdraw funds simultaneously due to fear that a bank may fail. Because banks hold only a fraction of deposits as liquid reserves, this behaviour can cause a liquidity crisis and potentially trigger collapse.

This project uses simulation modelling to explore how depositor behaviour, confidence, and reserve policies interact to create systemic financial risk.

The goal was to build a flexible simulation that allows different economic and behavioural parameters to be tested and analysed across multiple scenarios.

🎯 Project Objectives
Model depositor withdrawal behaviour
Simulate bank liquidity under stress
Analyse how confidence shocks trigger cascading withdrawals
Identify tipping points that lead to bank runs
Explore the relationship between reserve ratios and stability
🧠 Simulation Concept

The simulation represents interactions between:

Depositors

Each depositor has a withdrawal threshold
Decisions are influenced by confidence and behaviour of others
Panic can spread through the system

Bank

Holds limited liquid reserves
Must satisfy withdrawal demand
Can become illiquid if withdrawals exceed reserves

The system evolves over multiple iterations to observe emergent behaviour.

⚙️ Key Parameters

Experiments were conducted by varying:

Reserve ratio
Number of depositors
Withdrawal thresholds
Confidence / panic levels
External “shock” events

By running multiple simulations, patterns and risk factors were identified.

🔬 Methodology
Define model parameters
Run repeated simulations with varying inputs
Collect and analyse outcomes
Identify scenarios that lead to bank runs

This approach allows exploration of complex systems that are difficult to study analytically.

📊 Example Research Questions
How much liquidity is required to prevent a bank run?
How sensitive is the system to changes in depositor confidence?
Can small shocks trigger large-scale withdrawal cascades?
What parameter combinations create the highest systemic risk?
🛠️ Skills Demonstrated
Python programming
Simulation modelling
Data analysis and experimentation
Financial risk modelling
Research and analytical thinking
🚀 Motivation

This project combines computer science and finance to demonstrate how computational models can be used to explore real-world economic behaviour and systemic risk.
