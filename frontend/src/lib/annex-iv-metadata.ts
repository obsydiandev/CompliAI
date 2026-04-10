export interface FieldMeta {
  key: string
  label: string
  type: 'text' | 'textarea' | 'array'
  required: boolean
  help?: string
}

export interface SectionMeta {
  number: number
  name: string
  description: string
  fields: FieldMeta[]
}

export const ANNEX_IV_SECTION_METADATA: SectionMeta[] = [
  {
    number: 1,
    name: 'General Description',
    description:
      'A general description of the AI system including its intended purpose, the persons responsible for it, and its basic characteristics.',
    fields: [
      {
        key: 'intended_purpose',
        label: 'Intended Purpose',
        type: 'textarea',
        required: true,
        help: 'Describe the specific purpose for which the AI system is intended, including the specific context of use.',
      },
      {
        key: 'responsible_persons',
        label: 'Responsible Persons',
        type: 'textarea',
        required: true,
        help: 'Names and contact details of the provider and, where applicable, the authorised representative.',
      },
      {
        key: 'basic_characteristics',
        label: 'Basic Characteristics',
        type: 'textarea',
        required: true,
        help: 'Description of the key characteristics and capabilities of the AI system.',
      },
      {
        key: 'deployment_countries',
        label: 'Deployment Countries',
        type: 'array',
        required: false,
        help: 'List of EU member states where the system is intended to be deployed.',
      },
    ],
  },
  {
    number: 2,
    name: 'System Architecture & Technical Specifications',
    description:
      'A description of the elements of the AI system and of the process for its development, including the overall logic and the principal design choices.',
    fields: [
      {
        key: 'system_architecture',
        label: 'System Architecture',
        type: 'textarea',
        required: true,
        help: 'Describe the overall architecture and technical design of the AI system.',
      },
      {
        key: 'algorithms_used',
        label: 'Algorithms Used',
        type: 'array',
        required: true,
        help: 'List of machine learning algorithms and techniques employed.',
      },
      {
        key: 'model_type',
        label: 'Model Type',
        type: 'text',
        required: true,
        help: 'e.g., neural network, decision tree, ensemble, LLM.',
      },
      {
        key: 'framework_and_tools',
        label: 'Frameworks & Tools',
        type: 'array',
        required: false,
        help: 'Software frameworks, libraries, and tools used (e.g., TensorFlow, PyTorch).',
      },
      {
        key: 'hardware_requirements',
        label: 'Hardware Requirements',
        type: 'textarea',
        required: false,
        help: 'Describe the computational hardware needed for training and inference.',
      },
    ],
  },
  {
    number: 3,
    name: 'Training Data & Methodology',
    description:
      'Detailed information about the training, validation, and testing data used, including data governance practices.',
    fields: [
      {
        key: 'training_datasets',
        label: 'Training Datasets',
        type: 'textarea',
        required: true,
        help: 'Description of datasets used for training including sources, size, and characteristics.',
      },
      {
        key: 'data_collection_methodology',
        label: 'Data Collection Methodology',
        type: 'textarea',
        required: true,
        help: 'How was training data collected and pre-processed?',
      },
      {
        key: 'data_governance',
        label: 'Data Governance Practices',
        type: 'textarea',
        required: true,
        help: 'Data governance measures including quality checks, bias assessment, and privacy protections.',
      },
      {
        key: 'validation_datasets',
        label: 'Validation Datasets',
        type: 'textarea',
        required: true,
        help: 'Description of datasets used for validation.',
      },
      {
        key: 'test_datasets',
        label: 'Test Datasets',
        type: 'textarea',
        required: true,
        help: 'Description of datasets used for final testing.',
      },
      {
        key: 'known_data_limitations',
        label: 'Known Data Limitations',
        type: 'textarea',
        required: false,
        help: 'Any known limitations, biases, or gaps in the training data.',
      },
    ],
  },
  {
    number: 4,
    name: 'Performance Metrics & Benchmarks',
    description:
      'Description of the monitoring and logging capabilities, including performance metrics and accuracy levels.',
    fields: [
      {
        key: 'accuracy_metrics',
        label: 'Accuracy Metrics',
        type: 'textarea',
        required: true,
        help: 'Accuracy, precision, recall, F1 score, or other relevant performance metrics.',
      },
      {
        key: 'benchmark_datasets',
        label: 'Benchmark Datasets',
        type: 'array',
        required: false,
        help: 'Standard benchmarks used to evaluate the system.',
      },
      {
        key: 'performance_thresholds',
        label: 'Performance Thresholds',
        type: 'textarea',
        required: true,
        help: 'Minimum acceptable performance levels and conditions for deployment.',
      },
      {
        key: 'known_limitations',
        label: 'Known Limitations',
        type: 'textarea',
        required: true,
        help: 'Known performance limitations, edge cases, and failure modes.',
      },
    ],
  },
  {
    number: 5,
    name: 'Risk Management',
    description:
      'Description of the risk management system, including risk identification, assessment, and mitigation measures.',
    fields: [
      {
        key: 'risk_identification',
        label: 'Risk Identification',
        type: 'textarea',
        required: true,
        help: 'Identified risks associated with the AI system across its lifecycle.',
      },
      {
        key: 'risk_assessment',
        label: 'Risk Assessment',
        type: 'textarea',
        required: true,
        help: 'Assessment of the likelihood and severity of identified risks.',
      },
      {
        key: 'mitigation_measures',
        label: 'Mitigation Measures',
        type: 'textarea',
        required: true,
        help: 'Technical and organisational measures to mitigate identified risks.',
      },
      {
        key: 'residual_risks',
        label: 'Residual Risks',
        type: 'textarea',
        required: false,
        help: 'Risks that remain after mitigation measures have been applied.',
      },
      {
        key: 'risk_monitoring_process',
        label: 'Risk Monitoring Process',
        type: 'textarea',
        required: true,
        help: 'Ongoing process for monitoring risks post-deployment.',
      },
    ],
  },
  {
    number: 6,
    name: 'Human Oversight & Control',
    description:
      'Description of the human oversight measures, including the design choices and technical measures enabling human oversight.',
    fields: [
      {
        key: 'oversight_mechanisms',
        label: 'Oversight Mechanisms',
        type: 'textarea',
        required: true,
        help: 'Technical and organisational measures enabling human oversight of the AI system.',
      },
      {
        key: 'human_intervention_points',
        label: 'Human Intervention Points',
        type: 'textarea',
        required: true,
        help: 'Points in the system operation where humans can intervene or override decisions.',
      },
      {
        key: 'override_capabilities',
        label: 'Override Capabilities',
        type: 'textarea',
        required: true,
        help: 'Description of how human operators can override, correct, or shut down the system.',
      },
      {
        key: 'operator_training_requirements',
        label: 'Operator Training Requirements',
        type: 'textarea',
        required: false,
        help: 'Required training and competences for operators and deployers.',
      },
    ],
  },
  {
    number: 7,
    name: 'Transparency & Explainability',
    description:
      'Description of the transparency and explainability features, including information to be provided to deployers and affected persons.',
    fields: [
      {
        key: 'explainability_approach',
        label: 'Explainability Approach',
        type: 'textarea',
        required: true,
        help: 'Methods used to explain AI system decisions to operators and affected persons.',
      },
      {
        key: 'output_interpretation',
        label: 'Output Interpretation',
        type: 'textarea',
        required: true,
        help: 'How system outputs should be interpreted and their degree of certainty.',
      },
      {
        key: 'disclosure_mechanisms',
        label: 'Disclosure Mechanisms',
        type: 'textarea',
        required: true,
        help: 'Mechanisms for disclosing AI involvement to affected persons where required.',
      },
      {
        key: 'instructions_for_use',
        label: 'Instructions for Use',
        type: 'textarea',
        required: true,
        help: 'Clear instructions for deployers on how to use the system appropriately.',
      },
    ],
  },
  {
    number: 8,
    name: 'Cybersecurity & Robustness',
    description:
      'Description of the measures to ensure cybersecurity, including resilience against attacks and technical robustness.',
    fields: [
      {
        key: 'security_measures',
        label: 'Security Measures',
        type: 'textarea',
        required: true,
        help: 'Technical security measures protecting the AI system from unauthorised access and manipulation.',
      },
      {
        key: 'adversarial_robustness',
        label: 'Adversarial Robustness',
        type: 'textarea',
        required: true,
        help: 'Measures to ensure robustness against adversarial inputs and data poisoning.',
      },
      {
        key: 'incident_response',
        label: 'Incident Response Plan',
        type: 'textarea',
        required: true,
        help: 'Process for responding to security incidents and system failures.',
      },
      {
        key: 'backup_and_recovery',
        label: 'Backup & Recovery',
        type: 'textarea',
        required: false,
        help: 'Backup procedures and recovery capabilities.',
      },
      {
        key: 'penetration_testing',
        label: 'Penetration Testing',
        type: 'textarea',
        required: false,
        help: 'Results of any security testing or penetration testing conducted.',
      },
    ],
  },
  {
    number: 9,
    name: 'Post-Market Monitoring & Incident Reporting',
    description:
      'Description of post-market monitoring plan and the process for reporting serious incidents to authorities.',
    fields: [
      {
        key: 'monitoring_plan',
        label: 'Post-Market Monitoring Plan',
        type: 'textarea',
        required: true,
        help: 'Plan for ongoing monitoring of the AI system after deployment.',
      },
      {
        key: 'performance_indicators',
        label: 'Performance Indicators',
        type: 'array',
        required: true,
        help: 'KPIs and metrics tracked in post-market monitoring.',
      },
      {
        key: 'incident_reporting_process',
        label: 'Incident Reporting Process',
        type: 'textarea',
        required: true,
        help: 'Process for identifying, documenting, and reporting serious incidents to authorities.',
      },
      {
        key: 'feedback_mechanisms',
        label: 'Feedback Mechanisms',
        type: 'textarea',
        required: false,
        help: 'Channels for receiving feedback from deployers and affected persons.',
      },
      {
        key: 'update_and_retraining_policy',
        label: 'Update & Retraining Policy',
        type: 'textarea',
        required: false,
        help: 'Policy for when and how the AI system is updated or retrained.',
      },
    ],
  },
]
