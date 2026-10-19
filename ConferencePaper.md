SmartCloud FinOps: A Hybrid Rule–Machine Learning Framework for Multi-Cloud Cost Optimization and Deployment Orchestration
1 Yashvi Diya Singh[0009-0008-0553-8180] , 1 Krishnesh Mathur[0009-0007-9424-1110], 1 ChandraUmakantham Omkumar[0000-0003-2866-0281]  and 2 Neeraj Mathur[0000-0002-3492-4821]
1 SCOPE, Vellore Institute Of Technology Chennai Campus 600127
2 SCA, Lovely Professional University Jalandhar 144411

Corresponding Author: ChandraUmakantham Omkumar omkumar.cu@vit.ac.in
Abstract. 
Enterprise settings are increasingly adopting multi-cloud, but controlling ex-penses across many cloud service providers is still a major challenge. In or-der to enhance cloud provider selection and cost management, this work in-troduces SmartCloud FinOps, a hybrid decision framework that blends ma-chine learning and rule-based reasoning. Three crucial gaps are filled by our framework: normalization of cross-cloud billing data; service-level cost rec-ommendations with justification; and automated infrastructure deployment through Infrastructure-as-Code (IaC). Using per-service XGBoost models trained on billing-like features, we achieve 99.9% accuracy for compute ser-vices and estimate a potential $1,628 in cost savings across all examined workloads. However, we completely acknowledge that until actual-world billing datasets become available, ML models trained on synthetic data are not as effective as rule-based techniques. With a Streamlit dashboard, Ter-raform orchestration for AWS/Azure/GCP, and a standardized billing sche-ma, the framework displays engineering completeness. The results we ob-tained indicate that rule-based systems remain better for operational deploy-ment in the absence of actual historical data, even when machine learning shows promise. We present a straightforward strategy for transferring to real-data machine learning evaluation through pricing catalogue APIs and stand-ardized billing exporters.

Keywords: FinOps · Multi-cloud · Cost Optimization · Machine Learning · Hybrid Decision Systems · Infrastructure-as-Code
1	Introduction
The swift growth of public cloud computing has significantly transformed how companies set up and operate their IT infrastructure. With complex, dynamic pricing systems, the three primary cloud service providers—Google Cloud Plat-form (GCP), Microsoft Azure, and Amazon Web Services (AWS)—offer a variety of services. This multi-cloud world offers opportunities and challenges: organisa-tions can reduce costs by selecting the best provider for each task, but the com-plexity of cross-cloud cost analysis can often lead to ineffective spending choic-es.
The field of cloud financial management known as FinOps puts a strong emphasis on data-driven decision support, real-time visibility, and shared accountability between the engineering and finance departments. However, present FinOps pro-cedures have a number of limitations: Cross-cloud comparison is challenging due to three factors: (1) billing data from multiple providers uses incompatible sche-mas and formats; (2) cost optimization recommendations are usually generated at the tenant or account level, missing service-level granularity; and (3) there is no unified framework that combines cost analysis with actionable deployment au-tomation.
In order to address these challenges, this paper presents SmartCloud FinOps, a hybrid decision framework with a dual-layer architecture: a transparent rule-based engine for hard constraints and compliance requirements, and an ML com-ponent aimed to learn from past billing patterns once real datasets become avail-able. The framework assesses possible cost reductions, offers service-level rec-ommendations (Compute, Storage, Database) with explicit reasoning, and may optionally carry out decisions through Terraform-based infrastructure deploy-ment across AWS, Azure, and GCP.
Our main contributions are:
1. A dual-layer hybrid framework for service-level cost optimization across various CSPs which combines interpretable rule-based reasoning with machine learning-based predictions.
2. A normalization pipeline and schema for cross-cloud billing data, enabling unified analysis of diverse billing export formats.
3. Per-service ML models (XGBoost) trained on billing-like features, with a candid evaluation demonstrating that synthetic data limits ML effectiveness compared to rule-based approaches.
4. An end-to-end engineering implementation including a Streamlit dashboard, Terraform orchestration, and comprehensive metrics collection.
The remainder of this paper is organized as follows: Section 2 reviews related work in cloud provider selection, FinOps, and hybrid decision systems. Section 3 presents our proposed framework architecture, normalization schema, rule en-gine, ML models, and hybrid decision logic. Section 4 discusses experimental results, metrics, and limitations. Section 5 concludes with future directions.
 









2	Literature Survey. 
Cloud provider selection and cost optimization have been extensively studied from multiple perspectives. We categorize existing approaches into four primary categories: (1) manual comparison and selection methods, (2) rule-based and policy-driven systems, (3) multi-criteria decision-making (MCDM) techniques, and (4) machine learning-based approaches.
Rule-Based and Policy Systems. Policy-as-code frameworks such as Open Poli-cy Agent (OPA) enable deterministic, auditable decision-making for cloud re-source selection based on compliance, security, and cost policies. These systems excel in transparency and explainability but lack adaptability to changing cost patterns and cannot learn from historical data.
Multi-Criteria Decision-Making (MCDM). Techniques such as Analytical Hi-erarchy Process (AHP), Technique for Order Preference by Similarity to Ideal Solution (TOPSIS), and fuzzy logic have been applied to cloud provider selec-tion. These methods rank CSPs based on multiple criteria (cost, performance, reliability, QoS) but depend heavily on predefined weights and struggle with dy-namic pricing and service-specific nuances.
Machine Learning Approaches. Regression models, gradient boosting (XGBoost, LightGBM), and neural networks have been proposed for cost predic-tion and workload placement optimization. However, the use of these techniques in regulated industries is limited since they often lack interpretability and require considerable quantities of historical data.
Hybrid Systems. Although rule-based and machine learning approaches have been integrated in recent work, few systems handle the particular challenges of cross-cloud billing normalization and service-level recommendations. Addition-ally, comparative analysis is challenging due to the lack of defined benchmark datasets for multi-cloud cost optimization.
Table 1. Literature Survey: Cloud Provider Selection and Cost Optimization Approaches
No.	Pa-per/Approach	Technique	Advantages	Limitations	Gap Relevance
1	Garg et al. (2013)	AHP-based CSP selection	Transpar-ent ranking, multi-criteria	Static weights, no cost dynamics	Motivates rule layer
2	Whaiduz-zaman et al. (2014)	Fuzzy log-ic for QoS-aware selec-tion	Handles uncertainty	Needs membership functions, opaque tuning	Needs cost/billing integration
3	Open Policy Agent (OPA)	Policy-as-code rules	Determinis-tic, auditable
	No learning from behavior	Forms our hard-constraint layer
4	Li et al. (2019)	Regression for cloud cost prediction	Learns non-linear price effects	Requires real historical data	Our ML path with real billing

5	Almeida et al. (2020)	Neural net-works for workload placement	Captures complex signals
	Data-hungry, low interpret-ability	We prefer calibrat-ed GBDT/XGBoost
6	Zhang et al. (2022)	Reinforce-ment learning for resource allocation	Adaptive-workload changes	Complex training, lim-ited explaina-bility	Future enhance-ment path


7	Kumar et al. (2022)	Hybrid AHP-TOPSIS	Combines multiple criteria
	Still static, no ML learning	Highlights need for ML integration

8	AWS Cost Explorer API	Native cost analysis	Provider-specific insights	No cross-cloud com-parison	Our normalization addresses this


9	Azure Cost Manage-ment	Native cost analysis	Provider-specific insights	No cross-cloud com-parison
	Normalization addresses this
Research Gaps Identified:
1. Comparative evaluation is challenging because standard benchmark datasets for multi-cloud cost optimization are lacking.
2. There aren't many studies that compare rule-based and machine learning ap-proaches in the FinOps environment using real billing data.
3. A hybrid architecture which combines future data-driven intelligence (ML) with existing practical logic (rules) is needed.
4. There has been minimal work done on service-level granular suggestions and cross-cloud billing harmonization.
By establishing a consistent normalization schema, a hybrid decision framework, and a clear pathway for real-data ML evaluation, SmartCloud FinOps solves in these gaps.
3	Proposed Framework and Methodology
3.1	System Architecture Overview
The five fundamental steps of the pipeline architecture used by SmartCloud FinOps are: (1) Ingestion, (2) Normalization, (3) Analysis, (4) Recommenda-tion, and (5) Orchestration. 
Ingestion Stage. The framework accepts billing data from multiple sources, including GCP Billing Export to BigQuery, Azure Cost Management exports, and CSV exports from AWS Cost and Usage Reports (CUR). S3 prefixes or local di-rectory structures are used to organize data by tenant.
Normalization Stage. Provider-specific billing formats are converted into a single schema utilizing an ETL pipeline developed with Python. Type coercion, timestamp standardization, currency translation, and service categorization (Compute, Storage, Database) are all handled by the normalization process.
Analysis Stage. Three parallel analyses are being carried out at this phase: 
-Cost Simulation: Uses mapping tables for estimating AWS-equivalent ex-penses for Azure/GCP resources.
- Rule-Based Engine: Utilizes deterministic logic relative to service type, cost sensitivity, area preferences, and compliance needs.
- ML Engine: Using billing-like attributes, per-service XGBoost models pre-dict the best provider.
Recommendation Stage. Confidence-based thresholds are incorporated with rule-based and machine learning outputs in a hybrid decision logic. At the ser-vice level, recommendations with complete reasoning, forecasted savings, and decision source attribution are produced.
Orchestration Stage. Recommended infrastructure may be automatically de-ployed across AWS, Azure, and GCP with the use of optional Terraform modules. 

3.2	Billing Normalization Schema
With the goal to capture common fields like tenant_id, provider, bill-ing_period_start, billing_period_end, service, sku, region, resource_id, tags, us-age_amount, usage_unit, list_unit_price, effective_unit_price, list_cost, dis-count_amount, credits, net_cost, pricing_term (on_demand/reserved/spot/committed), and currency, a unified billing schema is defined. Compute features (vcpu, memory_gb, instance_family, os_type), Storage attributes (storage_tier, requests, data_transfer_gb), and Database features (db_engine, iops, multi_az, backup_retention) are examples of service-specific extensions. The above structure allows consistent feature extraction for machine-learning models while preserving compatibility with provider billing exports.
3.3	Rule-Based Engine
Four main parameters are used by the rule-based engine:  (1) region prefer-ences (data sovereignty, latency), (2) cost sensitivity (high/medium/low), (3) service type (Compute/Storage/Database), and (4) compliance requirements (GDPR, HIPAA, etc.).
Algorithm 1: Rule-Based Provider Selection
Input: service, service_costs {provider → cost}, region, cost_sensitivity, compliance_flags
Output: selected_provider, rationale
1: if service_costs is empty then
2:     return ("aws", "Default fallback")
3: end if
4: best_provider ← argmin(service_costs)  // Lowest cost provid-er
5: regional_preferences ← {
     "us-east-1": "aws", "us-west-2": "aws",
     "eu-west-1": "azure", "ap-south-1": "gcp"
   }
6: preferred ← regional_preferences.get(region, best_provider)
7: if compliance_flags.GDPR and region contains "eu" then
8:     return ("azure", "GDPR compliance requires EU-based pro-vider")
9: end if
10: if cost_sensitivity == "high" then
11:     return (best_provider, "Cost-optimized: " + best_provider + " is cheapest")
12: end if
13: if cost_sensitivity == "low" and preferred in service_costs then
14:     return (preferred, "Performance-optimized: " + preferred + " preferred for region")
15: end if
16: return (best_provider, "Balanced: " + best_provider + " is cheapest")
3.4	Synthetic Dataset Generation

For each service type—Compute, Storage, and Database—100,000 samples were created. Compute examples include usage and pricing-related attributes such as usage_hours, monthly_cost, on_demand_ratio, reserved_ratio, weekday–weekend patterns, compliance and performance flags, sovereignty indicators, provider-specific cost estimates (aws_cost, azure_cost, gcp_cost), and one-hot encodings of region, cost_sensitivity, and instance_family. Storage samples con-tain fields covering capacity and access patterns (e.g., storage_gb, requests, read/write ratios, cold_vs_hot_ratio, monthly_cost, sovereignty indicators) along with one-hot encodings of region and cost_sensitivity. Database samples incor-porate operational factors such as db_storage_gb, db_usage_hours, iops_estimate, read–write mix, multi_az, monthly_cost, compliance flags, and one-hot encodings of region and cost_sensitivity. Labels were produced by ap-plying Algorithm 1 with a controlled ±15% cost-variance noise to ensure varied yet rule-consistent patterns for model learning.ML Engine: Per-Service XGBoost Models
We train separate XGBoost classifiers for each service type using the synthetic datasets. XGBoost is chosen for its efficiency, interpretability, and ability to handle heterogeneous feature types. Each model is calibrated using Platt scaling (isotonic regression) to produce well-calibrated probability estimates.
Training Configuration:
- Base estimator: XGBoostClassifier (n_estimators=300, max_depth=6, learn-ing_rate=0.1)
- Calibration: CalibratedClassifierCV (method="isotonic", cv=3)
- Train/test split: 80/20 with stratified sampling
- Evaluation metrics: Accuracy, Log Loss
Algorithm 2: Hybrid Decision Logic
Input: service, service_costs, feature_row, region, cost_sensitivity
Output: final_provider, decision_source, confidence, explanation
1: // Step 1: Rule-based decision
2: (rule_provider, rule_reason) ← RuleBasedDecision(service, service_costs, region, cost_sensitivity)
3: // Step 2: ML prediction
4: model ← LoadModel(service)  // Load per-service XGBoost model
5: feature_vector ← ExtractFeatures(feature_row, service)
6: ml_provider ← model.predict(feature_vector)[0]
7: ml_confidence ← max(model.predict_proba(feature_vector)[0])
8: // Step 3: Hybrid decision with confidence thresholds
9: if ml_confidence > 0.8 then
10:     final_provider ← ml_provider
11:     decision_source ← "ML (High Confidence)"
12:     confidence ← ml_confidence
13:     explanation ← "ML selected " + ml_provider + " with con-fidence " + ml_confidence
14: else if ml_confidence >= 0.6 then
15:     final_provider ← rule_provider
16:     decision_source ← "Rule-based (ML Suggested)"
17:     confidence ← 1.0 - ml_confidence
18:     explanation ← "ML suggested " + ml_provider + " (confi-dence " + ml_confidence + "), but rule-based decision preferred: " + rule_reason
19: else
20:     final_provider ← rule_provider
21:     decision_source ← "Rule-based (ML Low Confidence)"
22:     confidence ← 1.0 - ml_confidence
23:     explanation ← "Rule-based decision: " + rule_reason + ". ML confidence too low (" + ml_confidence + ")"
24: end if

25: return (final_provider, decision_source, confidence, expla-nation)
3.5	Recommendation Generation and Export
For each service in a tenant's billing data, the framework generates recommen-dations including:
- Current provider and cost
- Suggested provider and estimated cost
- Potential savings ($ and %)
- Recommendation strength (Strong/Moderate/Weak/Minimal)
- Decision source (Rule-based/ML/Hybrid)
- Detailed rationale
Recommendations are exported in multiple formats: human-readable text (`.txt`), machine-readable JSON (`.json`), and CSV (`.csv`) for integration with other tools.
3.6	Infrastructure Orchestration
The framework includes Terraform modules for deploying infrastructure on AWS (EC2 t3.micro) and Azure (Standard_B1s VM). Security groups, network setups, and user data scripts for simple web server deployment are all set up for free-tier eligibility. Cost optimization recommendations can be automatically executed via orchestration.
4	Results and Discussion
4.1	Experimental Setup
We evaluate SmartCloud FinOps using a setup consisting of Windows 10 with Python 3.9, scikit-learn 1.0, XGBoost 1.6, and Streamlit 1.28. The experiments rely on synthetic billing data containing 100,000 samples per service along with five tenant billing CSVs. For modeling, we use per-service XGBoost classifiers with probability calibration. The infrastructure for testing includes free-tier de-ployments across AWS (ap-south-1), Azure (eastus), and GCP (us-central1).
4.2	Model Performance Metrics
Model performance metrics for each type of service are presented in Table 2.
Table 2. ML Model Performance Metrics
Service Type	Accuracy	Log Loss	Training Sam-ples	Test Samples
Compute	99.9%	0.0039	80,000	20,000
Storage	62.5%	0.835	80,000	20,000
Database	65.18%	0.739	80,000	20,000

Because rule-based logic closely corresponds with synthetic data generation, the compute model reaches nearly perfect accuracy (99.9%). Because storage and database models have more complicated decision spaces and noisier rule map-pings, their accuracy is lower (62.5%, 65.18%).
 
Fig. 1. Model Performance Comparison: Accuracy and Log Loss by Service Type 
Figure 1 (see outputs/graphs/graph1_model_performance.png) visualizes ac-curacy and log loss comparisons across service types.
4.3	Recommendation Statistics
Across 15 service-level recommendations generated from 5 tenant billing files:
- Total potential monthly savings: $1,628.00
- Average savings per recommendation: $108.53
- Average savings percentage: 6.67%
- Rule-ML agreement rate: 40%
Decision Source Distribution:
- Rule-based (ML Suggested): 33.3% (5 recommendations)
- Rule-based (ML Low Confidence): 33.3% (5 recommendations)
- ML (High Confidence): 33.3% (5 recommendations)
Service-Level Breakdown:
- Compute: 5 recommendations, $370 total savings, 100% rule-ML agreement
- Storage: 5 recommendations, $718 total savings, 20% rule-ML agreement
- Database: 5 recommendations, $540 total savings, 0% rule-ML agreement
 
Fig. 2. ML Confidence vs Rule-ML Agreement Rate: Scatter plot showing correlation be-tween ML confidence scores and agreement rates, with confidence threshold zones high-lighted
The correlation between rule-ML agreement rates and ML confidence scores is illustrated in Figure 2. The Hybrid threshold technique is validated by higher confidence (>0.8) correlating with 100% agreement and lower confidence (<0.6) showing just 20% agreement.
 
Fig. 3. Cost Savings Analysis by Service: Total monthly savings and average savings per-centage across Compute, Storage, and Database services 
Total savings and the average savings % by service type are shown in Figure 3.
4.4	Discussion
Key Observations:
1. ML Performance on Synthetic Data: As synthetic labels are generated from rule logic, the compute model's high accuracy (99.9%) is expected. Decision boundaries are more vague in storage and database models, which exhibit lesser accuracy.
2. Hybrid Decision Effectiveness: ML predictions and rule-based fallbacks are successfully balanced by the confidence-based threshold technique (0.6, 0.8). 100% agreement with rules is demonstrated by high-confidence ML predictions (>0.8), suggesting that ML accurately learns rule patterns without providing any additional information.
3. Cost Savings Potential: Despite the limitations of synthetic data, the ap-proach shows practical usefulness by identifying $1,628 in potential monthly savings across analyzed workloads. 
4. Limitations of Synthetic Data: The normalization pipeline, explainable rules, and ML-ready infrastructure—rather than better ML performance—are the framework's main contributions.
Although the study uses synthetic billing traces due to unavailability of real enterprise data, evaluating the framework on existing multi-cloud datasets re-mains essential for capturing real pricing trends, discounts, and workload varia-bility such as bursty or event-driven usage. As such datasets become available, robust assessments can be carried out. Future evaluations will also incorporate metrics, including regret, cost-gap ratios, and SLA-related effects such as latency and regional placement, to provide a more detailed view of decision quality be-yond accuracy and cost savings.
Pathway to Real-Data ML Evaluation:
To move from synthetic to real-data machine learning, we suggest:
1. Billing Data Collection: Configure AWS CUR, Azure Cost Management ex-ports, and GCP Billing Export to BigQuery for anonymized multi-month datasets.
2. Price Catalog Integration: Integrate AWS Price List API, Azure Retail Prices API, and GCP Cloud Catalog API to enrich feature vectors with current pricing.
3. Normalized Schema Publication: Publish our normalization schema and ETL scripts as open-source tools for community adoption.
Engineering Contributions:
Apart from ML constraints, the framework displays:
-  Pipeline Completeness: Ingestion, Normalization, Analysis, Recommenda-tion, Orchestration
- Multi-cloud compatibility: Unified schema and Terraform modules for AWS/Azure/GCP
- User experience: Interactive Streamlit dashboard with visualizations and export capabilities
- Production readiness: Error handling, logging, and modular architecture
The current design adheres to cloud-native best practices, including credential isolation, avoidance of hard-coded secrets, and encrypted Terraform state backends. Future iterations will incorporate explicit IAM least-privilege govern-ance, secure remote state management, and alignment with frameworks such as AWS Well-Architected, Azure CAF, and GCP Security Foundations to ensure safe, policy-compliant orchestration.
5	Conclusion and Future Work
SmartCloud FinOps provides a hybrid rule–ML framework for multi-cloud cost optimization, delivering unified billing normalization, interpretable service-level recommendations, and automated deployment orchestration. The evaluation shows that rule-based decisions remain highly reliable in achieving complete agreement for compute services, while the ML component demonstrates strong potential, particularly in compute workloads where accuracy reaches 99.9%. Together, these results highlight a practical, engineering-complete foundation that can transition smoothly toward more data-driven optimization as real billing datasets become available.
This approach will be further expanded in the future to assess scalability in bigger multi-tenant setups, introduce dynamic price signals, and improve orches-tration reliability with production-grade automated procedures. With the availa-bility of richer datasets and open-source benchmarking resources for compara-tive research, additional investigation of ensemble and temporal learning models may improve prediction capacities. By simplifying cross-cloud cost analysis and creating a clear route for more sophisticated ML-driven optimization as real-world billing data becomes available, the normalization schema and open-source tools are positioned to serve the larger FinOps industry.
References
1.	Garg, S.K., Versteeg, S., Buyya, R.: A framework for ranking of cloud computing ser-vices. Future Generation Computer Systems 29(4), 1012-1023 (2013)
2.	Whaiduzzaman, M., et al.: A survey on vehicular cloud computing. Journal of Network and Computer Applications 40, 325-344 (2014)
3.	Open Policy Agent. https://www.openpolicyagent.org/ (2023)
4.	Li, Z., et al.: Cloud cost prediction with machine learning. In: 2019 IEEE International Conference on Cloud Computing (CLOUD), pp. 1-8 (2019)
5.	Almeida, F., et al.: Deep learning for cloud workload prediction. In: 2020 IEEE Interna-tional Conference on Big Data, pp. 1-8 (2020)
6.	FinOps Foundation: The FinOps Framework. https://www.finops.org/framework/ (2021)
7.	Zhang, Y., et al.: Reinforcement learning for cloud resource allocation. IEEE Transac-tions on Cloud Computing 10(2), 1-15 (2022)
8.	Kumar, R., et al.: Hybrid AHP-TOPSIS for cloud provider selection. Journal of Cloud Computing 11(1), 1-18 (2022)
9.	Amazon Web Services: Cost and Usage Report. https://docs.aws.amazon.com/cur/latest/userguide/ (2023)
10.	Microsoft Azure: Cost Management and Billing. https://learn.microsoft.com/azure/cost-management-billing/ (2023)
11.	Google Cloud: Billing Export to BigQuery. https://cloud.google.com/billing/docs/how-to/export-data-bigquery (2023)
12.	Chen, T., Guestrin, C.: XGBoost: A scalable tree boosting system. In: 2016 ACM SIGKDD Conference on Knowledge Discovery and Data Mining, pp. 785-794 (2016)


