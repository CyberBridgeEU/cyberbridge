# app/seeds/cobit_2019_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class Cobit2019Seed(BaseSeed):
    """Seed COBIT 2019 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating COBIT 2019 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create COBIT 2019 Framework
        cobit_2019_framework, created = self.get_or_create(
            models.Framework,
            {"name": "COBIT 2019", "organisation_id": default_org.id},
            {
                "name": "COBIT 2019",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("COBIT 2019 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == cobit_2019_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == cobit_2019_framework.id
            ).all()

            logger.info(f"Found existing COBIT 2019 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            return {
                "framework": cobit_2019_framework,
                "conformity_questions": existing_questions,
                "objectives": existing_objectives
            }

        # Get unique questions and objectives
        unique_conformity_questions = self._get_unique_conformity_questions()
        unique_objectives_data = self._get_unique_objectives()

        # Create conformity questions
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_conformity_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=conf_q_text,
                description="COBIT 2019 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=cobit_2019_framework.id,
                question_id=question.id,
                order=question_order
            )
            self.db.add(framework_question)

            question_order += 1

        # Create chapters and objectives
        chapters_dict = {}
        objectives_list = []

        for item in unique_objectives_data:
            chapter_title = item['chapter_title']

            # Create or get chapter
            if chapter_title not in chapters_dict:
                chapter, created = self.get_or_create(
                    models.Chapters,
                    {
                        "title": chapter_title,
                        "framework_id": cobit_2019_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": cobit_2019_framework.id
                    }
                )
                chapters_dict[chapter_title] = chapter

            chapter = chapters_dict[chapter_title]

            # Create objective
            objective, created = self.get_or_create(
                models.Objectives,
                {
                    "title": item['objective_title'],
                    "chapter_id": chapter.id
                },
                {
                    "title": item['objective_title'],
                    "subchapter": item.get('subchapter'),
                    "chapter_id": chapter.id,
                    "requirement_description": item.get('requirement_description')
                }
            )
            objectives_list.append(objective)

        self.db.commit()

        logger.info(f"Created COBIT 2019 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": cobit_2019_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return []

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM01.01: Evaluate the governance system.',
          'requirement_description': "Continually identify and engage with the enterprise's stakeholders, document an "
                                     'understanding of the requirements, and evaluate the current and future design of '
                                     'governance of enterprise I&T.',
          'subchapter': 'EDM01: Ensured Governance Framework Setting and Maintenance'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM01.02: Direct the governance system.',
          'requirement_description': 'Inform leaders on I&T governance principles and obtain their support, buy-in and '
                                     'commitment. Guide the structures, processes and practices for the governance of I&T in '
                                     'line with the agreed governance principles, decision-making models and authority levels. '
                                     'Define the information required for informed decision making.',
          'subchapter': 'EDM01: Ensured Governance Framework Setting and Maintenance'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM01.03: Monitor the governance system.',
          'requirement_description': 'Monitor the effectiveness and performance of the enterprise?s governance of I&T. Assess '
                                     'whether the governance system and implemented mechanisms (including structures, '
                                     'principles and processes) are operating effectively and provide appropriate oversight of '
                                     'I&T to enable value creation.',
          'subchapter': 'EDM01: Ensured Governance Framework Setting and Maintenance'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM02.01: Establish the target investment mix.',
          'requirement_description': 'Review and ensure clarity of the enterprise and I&T strategies and current services. '
                                     'Define an appropriate investment mix based on cost, alignment with strategy, type of '
                                     'benefit for the programs in the portfolio, degree of risk, and financial measures such '
                                     'as cost and expected return on investment (ROI) over the full economic life cycle. '
                                     'Adjust the enterprise and I&T strategies where necessary.',
          'subchapter': 'EDM02: Ensured Benefits Delivery'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM02.02: Evaluate value optimization.',
          'requirement_description': 'Continually evaluate the portfolio of I&T-enabled investments, services and assets to '
                                     'determine the likelihood of achieving enterprise objectives and delivering value. '
                                     'Identify and evaluate any changes in direction to management that will optimize value '
                                     'creation.',
          'subchapter': 'EDM02: Ensured Benefits Delivery'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM02.03: Direct value optimization.',
          'requirement_description': 'Direct value management principles and practices to enable optimal value realization '
                                     'from I&T-enabled investments throughout their full economic life cycle.',
          'subchapter': 'EDM02: Ensured Benefits Delivery'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM02.04: Monitor value optimization.',
          'requirement_description': 'Monitor key goals and metrics to determine whether the enterprise receives expected '
                                     'value and benefit from I&T-enabled investments and services. Identify significant issues '
                                     'and consider corrective actions.',
          'subchapter': 'EDM02: Ensured Benefits Delivery'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM03.01: Evaluate risk management.',
          'requirement_description': 'Continually examine and evaluate the effect of risk on the current and future use of I&T '
                                     "in the enterprise. Consider whether the enterprise's risk appetite is appropriate and "
                                     'ensure that risk to enterprise value related to the use of I&T is identified and '
                                     'managed.',
          'subchapter': 'EDM03: Ensured Risk Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM03.02: Direct risk management.',
          'requirement_description': 'Direct the establishment of risk management practices to provide reasonable assurance '
                                     'that I&T risk management practices are appropriate and that actual I&T risk does not '
                                     'exceed the board?s risk appetite.',
          'subchapter': 'EDM03: Ensured Risk Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM03.03: Monitor risk management.',
          'requirement_description': 'Monitor the key goals and metrics of the risk management processes. Determine how '
                                     'deviations or problems will be identified, tracked and reported for remediation.',
          'subchapter': 'EDM03: Ensured Risk Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM04.01: Evaluate resource management.',
          'requirement_description': 'Continually examine and evaluate the current and future need for business and I&T '
                                     'resources (financial and human), options for resourcing (including sourcing strategies), '
                                     'and allocation and management principles to meet the needs of the enterprise in the '
                                     'optimal manner.',
          'subchapter': 'EDM04: Ensured Resource Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM04.02: Direct resource management.',
          'requirement_description': 'Ensure the adoption of resource management principles to enable optimal use of business '
                                     'and I&T resources throughout their full economic life cycle.',
          'subchapter': 'EDM04: Ensured Resource Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM04.03: Monitor resource management.',
          'requirement_description': 'Monitor the key goals and metrics of the resource management processes. Determine how '
                                     'deviations or problems will be identified, tracked and reported for remediation.',
          'subchapter': 'EDM04: Ensured Resource Optimization'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM05.01: Evaluate stakeholder engagement and reporting requirements.',
          'requirement_description': 'Continually examine and evaluate current and future requirements for stakeholder '
                                     'engagement and reporting (including reporting mandated by regulatory requirements), and '
                                     'communication to other stakeholders. Establish principles for engaging and communicating '
                                     'with stakeholders.',
          'subchapter': 'EDM05: Ensured Stakeholder Engagement'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM05.02: Direct stakeholder engagement, communication and reporting.',
          'requirement_description': 'Ensure the establishment of effective stakeholder involvement, communication and '
                                     'reporting, including mechanisms for ensuring the quality and completeness of '
                                     'information, overseeing mandatory reporting, and creating a communication strategy for '
                                     'stakeholders.',
          'subchapter': 'EDM05: Ensured Stakeholder Engagement'},
         {'chapter_title': 'EDM: Evaluate, Direct and Monitor',
          'conformity_questions': [],
          'objective_title': 'EDM05.03: Monitor stakeholder engagement.',
          'requirement_description': 'Monitor stakeholder engagement levels and the effectiveness of stakeholder '
                                     'communication. Assess mechanisms for ensuring accuracy, reliability and effectiveness, '
                                     'and ascertain whether the requirements of different stakeholders in terms of reporting '
                                     'and communication are met.',
          'subchapter': 'EDM05: Ensured Stakeholder Engagement'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.01: Design the management system for enterprise I&T.',
          'requirement_description': 'Design a management system tailored to the needs of the enterprise. Management needs of '
                                     'the enterprise are defined through the use of the goals cascade and by application of '
                                     'design factors. Ensure the governance components are integrated and aligned with the '
                                     'enterprise?s governance and management philosophy and operating style.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.02: Communicate management objectives, direction and decisions made.',
          'requirement_description': 'Communicate awareness and promote understanding of alignment and I&T objectives to '
                                     'stakeholders throughout the enterprise. Communicate at regular intervals on important '
                                     'I&T-related decisions and their impact for the organization.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.03: Implement management processes (to support the achievement of governance and '
                             'management objectives).',
          'requirement_description': 'Define target process capability levels and implementation priority based on the '
                                     'management system design.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.04: Define and implement the organizational structures.',
          'requirement_description': 'Put in place the required internal and extended organizational structures (e.g., '
                                     'committees) per the management system design, enabling effective and efficient decision '
                                     'making. Ensure that required technology and information knowledge is included in the '
                                     'composition of management structures.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.05: Establish roles and responsibilities.',
          'requirement_description': 'Define and communicate roles and responsibilities for enterprise I&T, including '
                                     'authority levels, responsibilities and accountability.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.06: Optimize the placement of the IT function.',
          'requirement_description': 'Position the IT capabilities in the overall organizational structure to reflect the '
                                     'strategic importance and operational dependency of IT within the enterprise. The '
                                     'reporting line of the CIO and representation of IT within senior management should be '
                                     'commensurate with the importance of I&T within the enterprise.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.07: Define information (data) and system ownership.',
          'requirement_description': 'Define and maintain responsibilities for ownership of information (data) and information '
                                     'systems. Ensure that owners classify information and systems and protect them in line '
                                     'with their classification.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.08: Define target skills and competencies.',
          'requirement_description': 'Define the required skills and competencies to achieve relevant management objectives.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.09: Define and communicate policies and procedures.',
          'requirement_description': 'Put in place procedures to maintain compliance with and performance measurement of '
                                     'policies and other components of the control framework. Enforce the consequences of '
                                     'noncompliance or inadequate performance. Track trends and performance and consider these '
                                     'in the future design and improvement of the control framework.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.10: Define and implement infrastructure, services and applications to support the '
                             'governance and management system.',
          'requirement_description': 'Define and implement infrastructure, services and applications to support the governance '
                                     'and management system (e.g., architecture repositories, risk management system, project '
                                     'management tools, cost-tracking tools and incident monitoring tools).',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO01.11: Manage continual improvement of the I&T management system.',
          'requirement_description': 'Continually improve processes and other management system components to ensure that they '
                                     'can deliver against governance and management objectives. Consider COBIT implementation '
                                     'guidance, emerging standards, compliance requirements, automation opportunities and the '
                                     'feedback of stakeholders.',
          'subchapter': 'APO01: Managed I&T Management Framework'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.01: Understand enterprise context and direction.',
          'requirement_description': 'Understand the enterprise context (industry drivers, relevant regulations, basis for '
                                     'competition), its current way of working and its ambition level in terms of '
                                     'digitization.',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.02: Assess current capabilities, performance and digital maturity of the enterprise.',
          'requirement_description': 'Assess the performance of current I&T services and develop an understanding of current '
                                     'business and I&T capabilities (both internal and external). Assess current digital '
                                     'maturity of the enterprise and its appetite for change. ',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.03: Define target digital capabilities.',
          'requirement_description': 'Based on the understanding of enterprise context and direction, define the target I&T '
                                     'products and services and required capabilities. Consider reference standards, best '
                                     'practices and validated emerging technologies. ',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.04: Conduct a gap analysis.',
          'requirement_description': 'Identify gaps between current and target environments and describe the high-level '
                                     'changes in the enterprise architecture.',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.05: Define the strategic plan and road map.',
          'requirement_description': 'Develop a holistic digital strategy, in cooperation with relevant stakeholders, and '
                                     'detail a road map that defines the incremental steps required to achieve the goals and '
                                     'objectives. Ensure focus on the transformation journey through the appointment of a '
                                     'person who helps spearhead the digital transformation and drives alignment between '
                                     'business and I&T.',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO02.06: Communicate the I&T strategy and direction.',
          'requirement_description': 'Create awareness and understanding of the business and I&T objectives and direction, as '
                                     'captured in the I&T strategy, through communication to appropriate stakeholders and '
                                     'users throughout the enterprise.',
          'subchapter': 'APO02: Managed Strategy'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO03.01: Develop the enterprise architecture vision.',
          'requirement_description': 'The architecture vision provides a first-cut, high-level description of the baseline and '
                                     'target architectures, covering the business, information, data, application and '
                                     'technology domains. The architecture vision provides the sponsor with a key tool to sell '
                                     'the benefits of the proposed capabilities to stakeholders within the enterprise. The '
                                     'architecture vision describes how the new capabilities (in line with I&T strategy and '
                                     'objectives) will meet enterprise goals and strategic objectives and address stakeholder '
                                     'concerns when implemented.',
          'subchapter': 'APO03: Managed Enterprise Architecture'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO03.02: Define reference architecture.',
          'requirement_description': 'The reference architecture describes the current and target architectures for the '
                                     'business, information, data, application and technology domains.',
          'subchapter': 'APO03: Managed Enterprise Architecture'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO03.03: Select opportunities and solutions.',
          'requirement_description': 'Rationalize the gaps between baseline and target architectures, accounting for both '
                                     'business and technical perspectives, and logically group them into project work '
                                     'packages. Integrate the project with any related I&T-enabled investment programs to '
                                     'ensure that the architectural initiatives are aligned with and enable these initiatives '
                                     'as part of overall enterprise change. Make this a collaborative effort with key '
                                     "enterprise stakeholders from business and IT to assess the enterprise's transformation "
                                     'readiness, and identify opportunities, solutions and all implementation constraints.',
          'subchapter': 'APO03: Managed Enterprise Architecture'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO03.04: Define architecture implementation.',
          'requirement_description': 'Create a viable implementation and migration plan in alignment with the program and '
                                     'project portfolios. Ensure the plan is closely coordinated to deliver value and that the '
                                     'required resources are available to complete the necessary work.',
          'subchapter': 'APO03: Managed Enterprise Architecture'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO03.05: Provide enterprise architecture services.',
          'requirement_description': 'Provide enterprise architecture services within the enterprise that include guidance to '
                                     'and monitoring of implementation projects, formalizing ways of working through '
                                     "architecture contracts, and measuring and communicating architecture's value and "
                                     'compliance monitoring.',
          'subchapter': 'APO03: Managed Enterprise Architecture'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.01: Create an environment conducive to innovation.',
          'requirement_description': 'Create an environment that is conducive to innovation, considering methods such as '
                                     'culture, reward, collaboration, technology forums, and mechanisms to promote and capture '
                                     'employee ideas.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.02: Maintain an understanding of the enterprise environment.',
          'requirement_description': 'Work with relevant stakeholders to understand their challenges. Maintain an adequate '
                                     'understanding of enterprise strategy, competitive environment and other constraints, so '
                                     'that opportunities enabled by new technologies can be identified.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.03: Monitor and scan the technology environment.',
          'requirement_description': 'Set up a technology watch process to perform systematic monitoring and scanning of the '
                                     "enterprise's external environment to identify emerging technologies that have the "
                                     'potential to create value (e.g., by realizing the enterprise strategy, optimizing costs, '
                                     'avoiding obsolescence, and better enabling enterprise and I&T processes). Monitor the '
                                     'marketplace, competitive landscape, industry sectors, and legal and regulatory trends to '
                                     'be able to analyze emerging technologies or innovation ideas in the enterprise context.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.04: Assess the potential of emerging technologies and innovative ideas.',
          'requirement_description': 'Analyze identified emerging technologies and/or other I&T innovative suggestions to '
                                     'understand their business potential. Work with stakeholders to validate assumptions on '
                                     'the potential of new technologies and innovation.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.05: Recommend appropriate further initiatives.',
          'requirement_description': 'Evaluate and monitor the results of proof-of-concept initiatives and, if favorable, '
                                     'generate recommendations for further initiatives. Gain stakeholder support.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO04.06: Monitor the implementation and use of innovation.',
          'requirement_description': 'Monitor the implementation and use of emerging technologies and innovations during '
                                     'adoption, integration and for the full economic life cycle to ensure that the promised '
                                     'benefits are realized and to identify lessons learned.',
          'subchapter': 'APO04: Managed Innovation'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO05.01: Determine the availability and sources of funds.',
          'requirement_description': 'Determine potential sources of funds, different funding options and the implications of '
                                     'the funding source on the investment return expectations.',
          'subchapter': 'APO05: Managed Portfolio'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO05.02: Evaluate and select programs to fund.',
          'requirement_description': 'Based on requirements for the overall investment portfolio mix and the I&T strategic '
                                     'plan and road map, evaluate and prioritize program business cases and decide on '
                                     'investment proposals. Allocate funds and initiate programs.',
          'subchapter': 'APO05: Managed Portfolio'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO05.03: Monitor, optimize and report on investment portfolio performance.',
          'requirement_description': 'On a regular basis, monitor and optimize the performance of the investment portfolio and '
                                     'individual programs throughout the entire investment life cycle. Ensure continuous '
                                     'follow-up on the alignment of the portfolio with I&T strategy.',
          'subchapter': 'APO05: Managed Portfolio'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO05.04: Maintain portfolios.',
          'requirement_description': 'Maintain portfolios of investment programs and projects, I&T products and services, and '
                                     'I&T assets.',
          'subchapter': 'APO05: Managed Portfolio'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO05.05: Manage benefits achievement.',
          'requirement_description': 'Monitor the benefits of providing and maintaining appropriate I&T products, services and '
                                     'capabilities, based on the agreed and current business case.',
          'subchapter': 'APO05: Managed Portfolio'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO06.01: Manage finance and accounting.',
          'requirement_description': 'Establish and maintain a method to manage and account for all I&T-related costs, '
                                     'investments and depreciation as an integral part of enterprise financial systems and '
                                     'accounts. Report using the enterprise?s financial measurement systems.',
          'subchapter': 'APO06: Managed Budget and Costs'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO06.02: Prioritize resource allocation.',
          'requirement_description': 'Implement a decision-making process to prioritize the allocation of resources and '
                                     'establish rules for discretionary investments by individual business units. Include the '
                                     'potential use of external service providers and consider the buy, develop and rent '
                                     'options.',
          'subchapter': 'APO06: Managed Budget and Costs'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO06.03: Create and maintain budgets.',
          'requirement_description': 'Prepare a budget reflecting investment priorities based on the portfolio of I&T-enabled '
                                     'programs and I&T services.',
          'subchapter': 'APO06: Managed Budget and Costs'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO06.04: Model and allocate costs.',
          'requirement_description': 'Establish and use an I&T costing model based, for example, on the service definition. '
                                     'This approach ensures that allocation of costs for services is identifiable, measurable '
                                     'and predictable, and encourages the responsible use of resources, including those '
                                     'provided by service providers. Regularly review and benchmark the cost/chargeback model '
                                     'to maintain its relevance and appropriateness for evolving business and IT activities.',
          'subchapter': 'APO06: Managed Budget and Costs'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO06.05: Manage costs.',
          'requirement_description': 'Implement a cost management process that compares actual costs against budget. Costs '
                                     'should be monitored and reported. Deviations from budget should be identified in a '
                                     'timely manner and their impact on enterprise processes and services assessed.',
          'subchapter': 'APO06: Managed Budget and Costs'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.01: Acquire and maintain adequate and appropriate staffing.',
          'requirement_description': 'Evaluate internal and external staffing requirements on a regular basis or upon major '
                                     'changes to the enterprise or operational or IT environments to ensure that the '
                                     'enterprise has sufficient human resources to support enterprise goals and objectives.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.02: Identify key IT personnel.',
          'requirement_description': 'Identify key IT personnel. Use knowledge capture (documentation), knowledge sharing, '
                                     'succession planning and staff backup to minimize reliance on a single individual '
                                     'performing a critical job function.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.03: Maintain the skills and competencies of personnel.',
          'requirement_description': 'Define and manage the skills and competencies required of personnel. Regularly verify '
                                     'that personnel have the competencies to fulfill their roles on the basis of their '
                                     'education, training and/or experience. Verify that these competencies are being '
                                     'maintained, using qualification and certification programs where appropriate. Provide '
                                     'employees with ongoing learning and opportunities to maintain their knowledge, skills '
                                     'and competencies at a level required to achieve enterprise goals.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.04: Assess and recognize/reward employee job performance.',
          'requirement_description': 'Conduct timely, regular performance evaluations against individual objectives derived '
                                     'from enterprise goals, established standards, specific job responsibilities, and the '
                                     'skills and competency framework. Implement a remuneration/recognition process that '
                                     'rewards successful attainment of performance goals.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.05: Plan and track the usage of IT and business human resources.',
          'requirement_description': 'Understand and track the current and future demand for business and IT human resources '
                                     'with responsibilities for enterprise I&T. Identify shortfalls and provide input into '
                                     'sourcing plans, enterprise and IT recruitment processes, and business and IT recruitment '
                                     'processes.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO07.06: Manage contract staff.',
          'requirement_description': 'Ensure that consultants and contract personnel who support the enterprise with I&T '
                                     "skills know and comply with the organization's policies and meet agreed contractual "
                                     'requirements.',
          'subchapter': 'APO07: Managed Human Resources'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO08.01: Understand business expectations.',
          'requirement_description': 'Understand current business issues, objectives and expectations for I&T. Ensure that '
                                     'requirements are understood, managed and communicated, and their status agreed and '
                                     'approved.',
          'subchapter': 'APO08: Managed Relationships'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO08.02: Align I&T strategy with business expectations and identify opportunities for IT to '
                             'enhance the business.',
          'requirement_description': 'Align I&T strategies with current business objectives and expectations to enable IT to '
                                     'be a value-add partner for the business and a governance component for enhanced '
                                     'enterprise performance.',
          'subchapter': 'APO08: Managed Relationships'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO08.03: Manage the business relationship.',
          'requirement_description': 'Manage the relationship between the IT service organization and its business partners. '
                                     'Ensure that relationship roles and responsibilities are defined and assigned, and '
                                     'communication is facilitated.',
          'subchapter': 'APO08: Managed Relationships'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO08.04: Coordinate and communicate.',
          'requirement_description': 'Work with all relevant stakeholders and coordinate the end-to-end delivery of I&T '
                                     'services and solutions provided to the business.',
          'subchapter': 'APO08: Managed Relationships'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO08.05: Provide input to the continual improvement of services.',
          'requirement_description': 'Continually improve and evolve I&T-enabled services and service delivery to the '
                                     'enterprise to align with changing enterprise objectives and technology requirements.',
          'subchapter': 'APO08: Managed Relationships'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO09.01: Identify I&T services.',
          'requirement_description': 'Analyze business requirements and the degree to which I&T-enabled services and service '
                                     'levels support business processes. Discuss and agree with the business on potential '
                                     'services and service levels. Compare potential service levels against the current '
                                     'service portfolio; identify new or changed services or service level options.',
          'subchapter': 'APO09: Managed Service Agreements'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO09.02: Catalog I&T-enabled services.',
          'requirement_description': 'Define and maintain one or more service catalogues for relevant target groups. Publish '
                                     'and maintain live I&T-enabled services in the service catalogs.',
          'subchapter': 'APO09: Managed Service Agreements'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO09.03: Define and prepare service agreements.',
          'requirement_description': 'Define and prepare service agreements based on options in the service catalogues. '
                                     'Include internal operational agreements.',
          'subchapter': 'APO09: Managed Service Agreements'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO09.04: Monitor and report service levels.',
          'requirement_description': 'Monitor service levels, report on achievements and identify trends. Provide the '
                                     'appropriate management information to aid performance management.',
          'subchapter': 'APO09: Managed Service Agreements'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO09.05: Review service agreements and contracts.',
          'requirement_description': 'Conduct periodic reviews of the service agreements and revise when needed.',
          'subchapter': 'APO09: Managed Service Agreements'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO10.01: Identify and evaluate vendor relationships and contracts.',
          'requirement_description': 'Continuously search for and identify vendors and categorize them into type, significance '
                                     'and criticality. Establish criteria to evaluate vendors and contracts. Review the '
                                     'overall portfolio of existing and alternative vendors and contracts.',
          'subchapter': 'APO10: Managed Vendors'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO10.02: Select vendors.',
          'requirement_description': 'Select suppliers according to a fair and formal practice to ensure a viable best fit '
                                     'based on specified requirements. Requirements should be optimized with input from '
                                     'potential suppliers.',
          'subchapter': 'APO10: Managed Vendors'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO10.03: Manage vendor relationships and contracts.',
          'requirement_description': 'Formalize and manage the supplier relationship for each supplier. Manage, maintain and '
                                     'monitor contracts and service delivery. Ensure that new or changed contracts conform to '
                                     'enterprise standards and legal and regulatory requirements. Deal with contractual '
                                     'disputes.',
          'subchapter': 'APO10: Managed Vendors'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO10.04: Manage vendor risk.',
          'requirement_description': "Identify and manage risk relating to vendors' ability to continually provide secure, "
                                     'efficient and effective service delivery. This also includes the subcontractors or '
                                     'upstream vendors that are relevant in the service delivery of the direct vendor. ',
          'subchapter': 'APO10: Managed Vendors'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO10.05: Monitor vendor performance and compliance.',
          'requirement_description': 'Periodically review overall vendor performance, compliance to contract requirements and '
                                     'value for money. Address identified issues.',
          'subchapter': 'APO10: Managed Vendors'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO11.01: Establish a quality management system (QMS).',
          'requirement_description': 'Establish and maintain a quality management system (QMS) that provides a standard, '
                                     'formal and continuous approach to quality management of information. The QMS should '
                                     'enable technology and business processes to align with business requirements and '
                                     'enterprise quality management.',
          'subchapter': 'APO11: Managed Quality'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO11.02: Focus quality management on customers.',
          'requirement_description': 'Focus quality management on customers by determining their requirements and ensuring '
                                     'integration in quality management practices.',
          'subchapter': 'APO11: Managed Quality'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO11.03: Manage quality standards, practices and procedures and integrate quality management '
                             'into key processes and solutions.',
          'requirement_description': 'Identify and maintain standards, procedures and practices for key processes to guide the '
                                     'enterprise in meeting the intent of the agreed quality management standards (QMS). This '
                                     'activity should align with I&T control framework requirements. Consider certification '
                                     'for key processes, organizational units, products or services.',
          'subchapter': 'APO11: Managed Quality'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO11.04: Perform quality monitoring, control and reviews.',
          'requirement_description': 'Monitor the quality of processes and services on an ongoing basis, in line with quality '
                                     'management standards. Define, plan and implement measurements to monitor customer '
                                     'satisfaction with quality as well as the value provided by the quality management system '
                                     '(QMS). The information gathered should be used by the process owner to improve quality.',
          'subchapter': 'APO11: Managed Quality'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO11.05: Maintain continuous improvement.',
          'requirement_description': 'Maintain and regularly communicate an overall quality plan that promotes continuous '
                                     'improvement. The plan should define the need for, and benefits of, continuous '
                                     'improvement. Collect and analyze data about the quality management system (QMS) and '
                                     'improve its effectiveness. Correct nonconformities to prevent recurrence.',
          'subchapter': 'APO11: Managed Quality'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.01: Collect data.',
          'requirement_description': 'Identify and collect relevant data to enable effective I&T-related risk identification, '
                                     'analysis and reporting.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.02: Analyze risk.',
          'requirement_description': 'Develop a substantiated view on actual I&T risk, in support of risk decisions.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.03: Maintain a risk profile.',
          'requirement_description': 'Maintain an inventory of known risk and risk attributes, including expected frequency, '
                                     'potential impact and responses. Document related resources, capabilities and current '
                                     'control activities related to risk items.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.04: Articulate risk.',
          'requirement_description': 'Communicate information on the current state of I&T-related exposures and opportunities '
                                     'in a timely manner to all required stakeholders for appropriate response.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.05: Define a risk management action portfolio.',
          'requirement_description': 'Manage opportunities to reduce risk to an acceptable level as a portfolio.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO12.06: Respond to risk.',
          'requirement_description': 'Respond in a timely manner to materialized risk events with effective measures to limit '
                                     'the magnitude of loss.',
          'subchapter': 'APO12: Managed Risk'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO13.01: Establish and maintain an information security management system (ISMS).',
          'requirement_description': 'Establish and maintain an information security management system (ISMS) that provides a '
                                     'standard, formal and continuous approach to security and privacy management for '
                                     'information. Ensure that the system supports secure technology and business processes '
                                     'that are aligned with business requirements, enterprise security and enterprise privacy '
                                     'management.',
          'subchapter': 'APO13: Managed Security'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO13.02: Define and manage an information security risk treatment plan.',
          'requirement_description': 'Maintain an information security plan that describes how information security risk is to '
                                     'be managed and aligned with enterprise strategy and architecture. Ensure that '
                                     'recommendations for implementing security improvements are based on approved business '
                                     'cases, implemented as an integral part of services and solutions development, and '
                                     'operated as an integral part of business operation.',
          'subchapter': 'APO13: Managed Security'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO13.03: Monitor and review the information security management system (ISMS).',
          'requirement_description': 'Maintain and regularly communicate the need for, and benefits of, continuous improvement '
                                     'in information security. Collect and analyze data about the information security '
                                     'management system (ISMS), and improve its effectiveness. Correct nonconformities to '
                                     'prevent recurrence.',
          'subchapter': 'APO13: Managed Security'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': "APO14.01: Define and communicate the organization's data management strategy and roles and "
                             'responsibilities.',
          'requirement_description': "Define how to manage and improve the organization's data assets, in line with enterprise "
                                     'strategy and objectives. Communicate the data management strategy to all stakeholders. '
                                     'Assign roles and responsibilities to ensure that corporate data are managed as critical '
                                     'assets and the data management strategy is implemented and maintained in an effective '
                                     'and sustainable manner.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.02: Define and maintain a consistent business glossary.',
          'requirement_description': 'Create, approve, update and promote consistent business terms and definitions to foster '
                                     'shared data usage across the organization.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.03: Establish the processes and infrastructure for metadata management.',
          'requirement_description': 'Establish the processes and infrastructure for specifying and extending metadata about '
                                     "the organization's data assets, fostering and supporting data sharing, ensuring "
                                     'compliant use of data, improving responsiveness to business changes and reducing '
                                     'data-related risk.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.04: Define a data quality strategy.',
          'requirement_description': 'Define an integrated, organizationwide strategy to achieve and maintain the level of '
                                     'data quality (such as complexity, integrity, accuracy, completeness, validity, '
                                     'traceability and timeliness) required to support the business goals and objectives.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.05: Establish data profiling methodologies, processes and tools.',
          'requirement_description': 'Implement standardized data profiling methodologies, processes, practices, tools and '
                                     'templates that can be applied across multiple data repositories and data stores.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.06: Ensure a data quality assessment approach.',
          'requirement_description': 'Provide a systematic approach to measure and evaluate data quality according to '
                                     'processes and techniques, and against data quality rules.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.07: Define the data cleansing approach.',
          'requirement_description': 'Define the mechanisms, rules, processes, and methods to validate and correct data '
                                     'according to predefined business rules.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.08: Manage the life cycle of data assets.',
          'requirement_description': 'Ensure that the organization understands, maps, inventories and controls its data flows '
                                     'through business processes over the data life cycle, from creation or acquisition to '
                                     'retirement.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.09: Support data archiving and retention.',
          'requirement_description': 'Ensure that data maintenance satisfies organizational and regulatory requirements for '
                                     'availability of historical data. Ensure that legal and regulatory requirements for data '
                                     'archiving and retention are met.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'APO: Align, Plan and Organize',
          'conformity_questions': [],
          'objective_title': 'APO14.10: Manage data backup and restore arrangements.',
          'requirement_description': 'Manage availability of critical data to ensure operational continuity.',
          'subchapter': 'APO14: Managed Data'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.01: Maintain a standard approach for program management.',
          'requirement_description': 'Maintain a standard approach for program management that enables governance and '
                                     'management review, decision-making and delivery-management activities. These activities '
                                     'should focus consistently on business value and goals (i.e., requirements, risk, costs, '
                                     'schedule and quality targets).',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.02: Initiate a program.',
          'requirement_description': 'Initiate a program to confirm expected benefits and obtain authorization to proceed. '
                                     'This includes agreeing on program sponsorship, confirming the program mandate through '
                                     'approval of the conceptual business case, appointing program board or committee members, '
                                     'producing the program brief, reviewing and updating the business case, developing a '
                                     'benefits realization plan, and obtaining approval from sponsors to proceed.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.03: Manage stakeholder engagement.',
          'requirement_description': 'Manage stakeholder engagement to ensure an active exchange of accurate, consistent and '
                                     'timely information for all relevant stakeholders. This includes planning, identifying '
                                     'and engaging stakeholders and managing their expectations.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.04: Develop and maintain the program plan.',
          'requirement_description': 'Formulate a program to lay the initial groundwork. Position it for successful execution '
                                     'by formalizing the scope of the work and identifying deliverables that will satisfy '
                                     'goals and deliver value. Maintain and update the program plan and business case '
                                     'throughout the full economic life cycle of the program, ensuring alignment with '
                                     'strategic objectives and reflecting the current status and insights gained to date.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.05: Launch and execute the program.',
          'requirement_description': 'Launch and execute the program to acquire and direct the resources needed to accomplish '
                                     'the goals and benefits of the program as defined in the program plan. In accordance with '
                                     'stage-gate or release review criteria, prepare for stage-gate, iteration or release '
                                     'reviews to report progress and make the case for funding up to the following stage-gate '
                                     'or release review.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.06: Monitor, control and report on the program outcomes.',
          'requirement_description': 'Monitor and control performance against plan throughout the full economic life cycle of '
                                     'the investment, covering solution delivery at the program level and value/outcome at the '
                                     'enterprise level. Report performance to the program steering committee and the sponsors.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.07: Manage program quality.',
          'requirement_description': 'Prepare and execute a quality management plan, processes and practices that align with '
                                     'quality management standards (QMS). Describe the approach to program quality and '
                                     'implementation. The plan should be formally reviewed and agreed on by all parties '
                                     'concerned and incorporated into the integrated program plan.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.08: Manage program risk.',
          'requirement_description': 'Eliminate or minimize specific risk associated with programs through a systematic '
                                     'process of planning, identifying, analyzing, responding to, monitoring and controlling '
                                     'the areas or events with the potential to cause unwanted change. Define and record any '
                                     'risk faced by program management.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI01.09: Close a program.',
          'requirement_description': 'Remove the program from the active investment portfolio when there is agreement that the '
                                     'desired value has been achieved or when it is clear it will not be achieved within the '
                                     'value criteria set for the program.',
          'subchapter': 'BAI01: Managed Programs'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI02.01: Define and maintain business functional and technical requirements.',
          'requirement_description': 'Based on the business case, identify, prioritize, specify and agree on business '
                                     'information, functional, technical and control requirements covering the '
                                     'scope/understanding of all initiatives required to achieve the expected outcomes of the '
                                     'proposed I&T-enabled business solution.',
          'subchapter': 'BAI02: Managed Requirements Definition'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI02.02: Perform a feasibility study and formulate alternative solutions.',
          'requirement_description': 'Perform a feasibility study of potential alternative solutions, assess their viability '
                                     'and select the preferred option. If appropriate, implement the selected option as a '
                                     'pilot to determine possible improvements.',
          'subchapter': 'BAI02: Managed Requirements Definition'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI02.03: Manage requirements risk.',
          'requirement_description': 'Identify, document, prioritize and mitigate functional, technical and information '
                                     'processing-related risk associated with the enterprise requirements, assumptions and '
                                     'proposed solution.',
          'subchapter': 'BAI02: Managed Requirements Definition'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI02.04: Obtain approval of requirements and solutions.',
          'requirement_description': 'Coordinate feedback from affected stakeholders. At predetermined key stages, obtain '
                                     'approval and sign-off from the business sponsor or product owner regarding functional '
                                     'and technical requirements, feasibility studies, risk analyses and recommended '
                                     'solutions.',
          'subchapter': 'BAI02: Managed Requirements Definition'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.01: Design high-level solutions.',
          'requirement_description': 'Develop and document high-level designs for the solution in terms of technology, '
                                     'business processes and workflows. Use agreed and appropriate phased or rapid Agile '
                                     'development techniques. Ensure alignment with the I&T strategy and enterprise '
                                     'architecture. Reassess and update the designs when significant issues occur during '
                                     'detailed design or building phases, or as the solution evolves. Apply a user-centric '
                                     'approach; ensure that stakeholders actively participate in the design and approve each '
                                     'version.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.02: Design detailed solution components.',
          'requirement_description': 'Develop, document and elaborate detailed designs progressively. Use agreed and '
                                     'appropriate phased or rapid Agile development techniques, addressing all components '
                                     '(business processes and related automated and manual controls, supporting I&T '
                                     'applications, infrastructure services and technology products, and partners/suppliers). '
                                     'Ensure that the detailed design includes internal and external service level agreements '
                                     '(SLAs) and operational level agreements (OLAs).',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.03: Develop solution components.',
          'requirement_description': 'Develop solution components progressively in a separate environment, in accordance with '
                                     'detailed designs following standards and requirements for development and documentation, '
                                     'quality assurance (QA), and approval. Ensure that all control requirements in the '
                                     'business processes, supporting I&T applications and infrastructure services, services '
                                     'and technology products, and partner/vendor services are addressed.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.04: Procure solution components.',
          'requirement_description': 'Procure solution components, based on the acquisition plan, in accordance with '
                                     'requirements and detailed designs, architecture principles and standards, and the '
                                     "enterprise's overall procurement and contract procedures, QA requirements, and approval "
                                     'standards. Ensure that all legal and contractual requirements are identified and '
                                     'addressed by the vendor.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.05: Build solutions.',
          'requirement_description': 'Install and configure solutions and integrate with business process activities. During '
                                     'configuration and integration of hardware and infrastructure software, implement '
                                     'control, security, privacy and auditability measures to protect resources and ensure '
                                     'availability and data integrity. Update the product or services catalogue to reflect the '
                                     'new solutions.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.06: Perform quality assurance (QA).',
          'requirement_description': 'Develop, resource and execute a QA plan aligned with the QMS to obtain the quality '
                                     'specified in the requirements definition and in the enterprise?s quality policies and '
                                     'procedures.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.07: Prepare for solution testing.',
          'requirement_description': 'Establish a test plan and required environments to test the individual and integrated '
                                     'solution components. Include the business processes and supporting services, '
                                     'applications and infrastructure.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.08: Execute solution testing.',
          'requirement_description': 'During development, execute testing continually (including control testing), in '
                                     'accordance with the defined test plan and development practices in the appropriate '
                                     'environment. Engage business process owners and end users in the test team. Identify, '
                                     'log and prioritize errors and issues identified during testing.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.09: Manage changes to requirements.',
          'requirement_description': 'Track the status of individual requirements (including all rejected requirements) '
                                     'throughout the project life cycle. Manage the approval of changes to requirements.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.10: Maintain solutions.',
          'requirement_description': 'Develop and execute a plan for the maintenance of solution and infrastructure '
                                     'components. Include periodic reviews against business needs and operational '
                                     'requirements.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.11: Define IT products and services and maintain the service portfolio.',
          'requirement_description': 'Define and agree on new or changed IT products or services and service level options. '
                                     'Document new or changed product and service definitions and service level options to be '
                                     'updated in the products and services portfolio.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI03.12: Design solutions based on the defined development methodology.',
          'requirement_description': 'Design, develop and implement solutions with the appropriate development methodology '
                                     '(i.e., waterfall, Agile or bimodal I&T), in accordance with the overall strategy and '
                                     'requirements.',
          'subchapter': 'BAI03: Managed Solutions Identification and Build'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI04.01: Assess current availability, performance and capacity and create a baseline.',
          'requirement_description': 'Assess availability, performance and capacity of services and resources to ensure that '
                                     'cost-justifiable capacity and performance are available to support business needs and '
                                     'deliver against service level agreements (SLAs). Create availability, performance and '
                                     'capacity baselines for future comparison.',
          'subchapter': 'BAI04: Managed Availability and Capacity'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI04.02: Assess business impact.',
          'requirement_description': 'Identify important services to the enterprise. Map services and resources to business '
                                     'processes and identify business dependencies. Ensure that the impact of unavailable '
                                     'resources is fully agreed on and accepted by the customer. For vital business functions, '
                                     'ensure that availability requirements can be satisfied per service level agreement '
                                     '(SLA).',
          'subchapter': 'BAI04: Managed Availability and Capacity'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI04.03: Plan for new or changed service requirements.',
          'requirement_description': 'Plan and prioritize availability, performance and capacity implications of changing '
                                     'business needs and service requirements.',
          'subchapter': 'BAI04: Managed Availability and Capacity'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI04.04: Monitor and review availability and capacity.',
          'requirement_description': 'Monitor, measure, analyze, report and review availability, performance and capacity. '
                                     'Identify deviations from established baselines. Review trend analysis reports '
                                     'identifying any significant issues and variances. Initiate actions where necessary and '
                                     'ensure that all outstanding issues are addressed.',
          'subchapter': 'BAI04: Managed Availability and Capacity'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI04.05: Investigate and address availability, performance and capacity issues.',
          'requirement_description': 'Address deviations by investigating and resolving identified availability, performance '
                                     'and capacity issues.',
          'subchapter': 'BAI04: Managed Availability and Capacity'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.01: Establish the desire to change.',
          'requirement_description': 'Understand the scope and impact of the desired change. Assess stakeholder readiness and '
                                     'willingness to change. Identify actions that will motivate stakeholder acceptance and '
                                     'participation to make the change work successfully.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.02: Form an effective implementation team.',
          'requirement_description': 'Establish an effective implementation team by assembling appropriate members, creating '
                                     'trust, and establishing common goals and effectiveness measures.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.03: Communicate desired vision.',
          'requirement_description': 'Communicate the desired vision for the change in the language of those affected by it. '
                                     'The communication should be made by senior management and include the rationale for, and '
                                     'benefits of, the change; the impacts of not making the change; and the vision, the road '
                                     'map and the involvement required of the various stakeholders.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.04: Empower role players and identify short-term wins.',
          'requirement_description': 'Empower those with implementation roles by assigning accountability. Provide training '
                                     'and align organizational structures and HR processes. Identify and communicate '
                                     'short-term wins that are important from a change-enablement perspective.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.05: Enable operation and use.',
          'requirement_description': 'Plan and implement all technical, operational and usage aspects so all those who are '
                                     'involved in the future state environment can exercise their responsibility.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.06: Embed new approaches.',
          'requirement_description': 'Embed new approaches by tracking implemented changes, assessing the effectiveness of the '
                                     'operation and use plan, and sustaining ongoing awareness through regular communication. '
                                     'Take corrective measures as appropriate (which may include enforcing compliance).',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI05.07: Sustain changes.',
          'requirement_description': 'Sustain changes through effective training of new staff, ongoing communication '
                                     'campaigns, continued commitment of top management, monitoring of adoption and sharing of '
                                     'lessons learned across the enterprise.',
          'subchapter': 'BAI05: Managed Organizational Change'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI06.01: Evaluate, prioritize and authorize change requests.',
          'requirement_description': 'Evaluate all requests for change to determine the impact on business processes and I&T '
                                     'services, and to assess whether change will adversely affect the operational environment '
                                     'and introduce unacceptable risk. Ensure that changes are logged, prioritized, '
                                     'categorized, assessed, authorized, planned and scheduled.',
          'subchapter': 'BAI06: Managed IT Changes'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI06.02: Manage emergency changes.',
          'requirement_description': 'Carefully manage emergency changes to minimize further incidents. Ensure the emergency '
                                     'change is controlled and takes place securely. Verify that emergency changes are '
                                     'appropriately assessed and authorized after the change.',
          'subchapter': 'BAI06: Managed IT Changes'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI06.03: Track and report change status.',
          'requirement_description': 'Maintain a tracking and reporting system to document rejected changes and communicate '
                                     'the status of approved, in-process and complete changes. Make certain that approved '
                                     'changes are implemented as planned.',
          'subchapter': 'BAI06: Managed IT Changes'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI06.04: Close and document the changes.',
          'requirement_description': 'Whenever changes are implemented, update the solution, user documentation and procedures '
                                     'affected by the change.',
          'subchapter': 'BAI06: Managed IT Changes'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.01: Establish an implementation plan.',
          'requirement_description': 'Establish an implementation plan that covers system and data conversion, acceptance '
                                     'testing criteria, communication, training, release preparation, promotion to production, '
                                     'early production support, a fallback/back-up plan, and a post-implementation review. '
                                     'Obtain approval from relevant parties.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.02: Plan business process, system and data conversion.',
          'requirement_description': 'Prepare for business process, I&T service data and infrastructure migration as part of '
                                     'the enterprise?s development methods. Include audit trails and a recovery plan should '
                                     'the migration fail.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.03: Plan acceptance tests.',
          'requirement_description': 'Establish a test plan based on enterprisewide standards that define roles, '
                                     'responsibilities, and entry and exit criteria. Ensure that the plan is approved by '
                                     'relevant parties.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.04: Establish a test environment.',
          'requirement_description': 'Define and establish a secure test environment representative of the planned business '
                                     'process and IT operations environment in terms of performance, capacity, security, '
                                     'internal controls, operational practices, data quality, privacy requirements and '
                                     'workloads.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.05: Perform acceptance tests.',
          'requirement_description': 'Test changes independently, in accordance with the defined test plan, prior to migration '
                                     'to the live operational environment.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.06: Promote to production and manage releases.',
          'requirement_description': 'Promote the accepted solution to the business and operations. Where appropriate, run the '
                                     'solution as a pilot implementation or in parallel with the old solution for a defined '
                                     'period and compare behavior and results. If significant problems occur, revert to the '
                                     'original environment based on the fallback/back-up plan. Manage releases of solution '
                                     'components.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.07: Provide early production support.',
          'requirement_description': 'For an agreed period of time, provide early support to users and I&T operations to '
                                     'resolve issues and help stabilize the new solution.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI07.08: Perform a post-implementation review.',
          'requirement_description': 'Conduct a post-implementation review to confirm outcome and results, identify lessons '
                                     'learned, and develop an action plan. Evaluate actual performance and outcomes of the new '
                                     'or changed service against expected performance and outcomes anticipated by the user or '
                                     'customer.',
          'subchapter': 'BAI07: Managed IT Change Acceptance and Transitioning'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI08.01: Identify and classify sources of information for governance and management of I&T.',
          'requirement_description': 'Identify, validate and classify diverse sources of internal and external information '
                                     'required to enable governance and management of I&T, including strategy documents, '
                                     'incident reports and configuration information that progresses from development to '
                                     'operations before going live.',
          'subchapter': 'BAI08: Managed Knowledge'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI08.02: Organize and contextualize information into knowledge.',
          'requirement_description': 'Organize information based on classification criteria. Identify and create meaningful '
                                     'relationships among information elements and enable use of information. Identify owners, '
                                     'and leverage and implement enterprise-defined information levels of access to management '
                                     'information and knowledge resources.',
          'subchapter': 'BAI08: Managed Knowledge'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI08.03: Use and share knowledge.',
          'requirement_description': 'Propagate available knowledge resources to relevant stakeholders and communicate how '
                                     'these resources can be used to address different needs (e.g., problem solving, learning, '
                                     'strategic planning and decision making).',
          'subchapter': 'BAI08: Managed Knowledge'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI08.04: Evaluate and update or retire information.',
          'requirement_description': 'Measure the use and evaluate the currency and relevance of information. Update '
                                     'information or retire obsolete information.',
          'subchapter': 'BAI08: Managed Knowledge'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI09.01: Identify and record current assets.',
          'requirement_description': 'Maintain an up-to-date, accurate record of all I&T assets that are required to deliver '
                                     'services and that are owned or controlled by the organization with an expectation of '
                                     'future benefit (including resources with economic value, such as hardware or software). '
                                     'Ensure alignment with configuration management and financial management.',
          'subchapter': 'BAI09: Managed Assets'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI09.02: Manage critical assets.',
          'requirement_description': 'Identify assets that are critical in providing service capability. Maximize their '
                                     'reliability and availability to support business needs.',
          'subchapter': 'BAI09: Managed Assets'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI09.03: Manage the asset life cycle.',
          'requirement_description': 'Manage assets from procurement to disposal. Ensure that assets are utilized as '
                                     'effectively and efficiently as possible and are accounted for and physically protected '
                                     'until appropriately retired.',
          'subchapter': 'BAI09: Managed Assets'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI09.04: Optimize asset value.',
          'requirement_description': 'Regularly review the overall asset base to identify ways to optimize value in alignment '
                                     'with business needs.',
          'subchapter': 'BAI09: Managed Assets'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI09.05: Manage licenses.',
          'requirement_description': 'Manage software licenses to maintain the optimal number of licenses and support business '
                                     'requirements. Ensure that the number of licenses owned is sufficient to cover the '
                                     'installed software in use.',
          'subchapter': 'BAI09: Managed Assets'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI10.01: Establish and maintain a configuration model.',
          'requirement_description': 'Establish and maintain a logical model of the services, assets, infrastructure and '
                                     'recording of configuration items (CIs), including the relationships among them. Include '
                                     'the CIs considered necessary to manage services effectively and to provide a single, '
                                     'reliable description of the assets in a service.',
          'subchapter': 'BAI10: Managed Configuration'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI10.02: Establish and maintain a configuration repository and baseline.',
          'requirement_description': 'Establish and maintain a configuration management repository and create controlled '
                                     'configuration baselines.',
          'subchapter': 'BAI10: Managed Configuration'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI10.03: Maintain and control configuration items.',
          'requirement_description': 'Maintain an up-to-date repository of configuration items (CIs) by populating any '
                                     'configuration changes.',
          'subchapter': 'BAI10: Managed Configuration'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI10.04: Produce status and configuration reports.',
          'requirement_description': 'Define and produce configuration reports on status changes of configuration items.',
          'subchapter': 'BAI10: Managed Configuration'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI10.05: Verify and review integrity of the configuration repository.',
          'requirement_description': 'Periodically review the configuration repository and verify completeness and correctness '
                                     'against the desired target.',
          'subchapter': 'BAI10: Managed Configuration'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.01: Maintain a standard approach for project management.',
          'requirement_description': 'Maintain a standard approach for project management that enables governance and '
                                     'management review, decision-making and delivery-management activities. These activities '
                                     'should focus consistently on business value and goals (i.e., requirements, risk, costs, '
                                     'schedule and quality targets).',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.02: Start up and initiate a project.',
          'requirement_description': 'Define and document the nature and scope of the project to confirm and develop a common '
                                     'understanding of project scope among stakeholders. The definition should be formally '
                                     'approved by the project sponsors.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.03: Manage stakeholder engagement.',
          'requirement_description': 'Manage stakeholder engagement to ensure an active exchange of accurate, consistent and '
                                     'timely information that reaches all relevant stakeholders. This includes planning, '
                                     'identifying and engaging stakeholders and managing their expectations.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.04: Develop and maintain the project plan.',
          'requirement_description': 'Establish and maintain a formal, approved, integrated project plan (covering business '
                                     'and IT resources) to guide project execution and control throughout the life of the '
                                     'project. The scope of projects should be clearly defined and tied to building or '
                                     'enhancing business capability.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.05: Manage project quality.',
          'requirement_description': 'Prepare and execute a quality management plan, processes and practices that align with '
                                     'quality management standards (QMS). Describe the approach to project quality and '
                                     'implementation. The plan should be formally reviewed and agreed on by all parties '
                                     'concerned and incorporated into the integrated project plans.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.06: Manage project risk.',
          'requirement_description': 'Eliminate or minimize specific risk associated with projects through a systematic '
                                     'process of planning, identifying, analyzing, responding to, monitoring and controlling '
                                     'the areas or events with potential to cause unwanted change. Define and record any risk '
                                     'faced by project management.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.07: Monitor and control projects.',
          'requirement_description': 'Measure project performance against key project performance criteria such as schedule, '
                                     'quality, cost and risk. Identify any deviations from expected targets. Assess the impact '
                                     'of deviations on the project and overall program and report results to key stakeholders.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.08: Manage project resources and work packages.',
          'requirement_description': 'Manage project work packages by placing formal requirements on authorizing and accepting '
                                     'work packages and assigning and coordinating appropriate business and IT resources.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'BAI: Build, Acquire and Implement',
          'conformity_questions': [],
          'objective_title': 'BAI11.09: Close a project or iteration.',
          'requirement_description': 'At the end of each project, release or iteration, require the project stakeholders to '
                                     'ascertain whether the project, release or iteration delivered the required results in '
                                     'terms of capabilities and contributed as expected to program benefits. Identify and '
                                     'communicate any outstanding activities required to achieve planned results of the '
                                     'project and/or benefits of the program. Identify and document lessons learned for future '
                                     'projects, releases, iterations and programs.',
          'subchapter': 'BAI11: Managed Projects'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS01.01: Perform operational procedures.',
          'requirement_description': 'Maintain and perform operational procedures and operational tasks reliably and '
                                     'consistently.',
          'subchapter': 'DSS01: Managed Operations'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS01.02: Manage outsourced I&T services.',
          'requirement_description': 'Manage the operation of outsourced I&T services to maintain the protection of enterprise '
                                     'information and reliability of service delivery.',
          'subchapter': 'DSS01: Managed Operations'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS01.03: Monitor I&T infrastructure.',
          'requirement_description': 'Monitor the I&T infrastructure and related events. Store sufficient chronological '
                                     'information in operations logs to reconstruct and review time sequences of operations '
                                     'and other activities surrounding or supporting operations.',
          'subchapter': 'DSS01: Managed Operations'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS01.04: Manage the environment.',
          'requirement_description': 'Maintain measures for protection against environmental factors. Install specialized '
                                     'equipment and devices to monitor and control the environment.',
          'subchapter': 'DSS01: Managed Operations'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS01.05: Manage facilities.',
          'requirement_description': 'Manage facilities, including power and communications equipment, in line with laws and '
                                     'regulations, technical and business requirements, vendor specifications, and health and '
                                     'safety guidelines.',
          'subchapter': 'DSS01: Managed Operations'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.01: Define classification schemes for incidents and service requests.',
          'requirement_description': 'Define classification schemes and models for incidents and service requests.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.02: Record, classify and prioritize requests and incidents.',
          'requirement_description': 'Identify, record and classify service requests and incidents and assign a priority '
                                     'according to business criticality and service agreements.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.03: Verify, approve and fulfill service requests.',
          'requirement_description': 'Select the appropriate request procedures and verify that the service requests fulfill '
                                     'defined request criteria. Obtain approval, if required, and fulfill the requests.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.04: Investigate, diagnose and allocate incidents.',
          'requirement_description': 'Identify and record incident symptoms, determine possible causes, and allocate for '
                                     'resolution.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.05: Resolve and recover from incidents.',
          'requirement_description': 'Document, apply and test the identified solutions or workarounds. Perform recovery '
                                     'actions to restore the I&T-related service.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.06: Close service requests and incidents.',
          'requirement_description': 'Verify satisfactory incident resolution and/or fulfilment of requests, and close.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS02.07: Track status and produce reports.',
          'requirement_description': 'Regularly track, analyze and report incidents and fulfilment of requests. Examine trends '
                                     'to provide information for continual improvement.',
          'subchapter': 'DSS02: Managed Service Requests and Incidents'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS03.01: Identify and classify problems.',
          'requirement_description': 'Define and implement criteria and procedures to identify and report problems. Include '
                                     'problem classification, categorization and prioritization.',
          'subchapter': 'DSS03: Managed Problems'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS03.02: Investigate and diagnose problems.',
          'requirement_description': 'Investigate and diagnose problems using relevant subject matter experts to assess and '
                                     'analyze root causes.',
          'subchapter': 'DSS03: Managed Problems'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS03.03: Raise known errors.',
          'requirement_description': 'As soon as root causes of problems are identified, create known-error records, document '
                                     'appropriate workarounds and identify potential solutions.',
          'subchapter': 'DSS03: Managed Problems'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS03.04: Resolve and close problems.',
          'requirement_description': 'Identify and initiate sustainable solutions addressing the root cause. Raise change '
                                     'requests via the established change management process, if required, to resolve errors. '
                                     'Ensure that the personnel affected are aware of the actions taken and the plans '
                                     'developed to prevent future incidents from occurring.',
          'subchapter': 'DSS03: Managed Problems'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS03.05: Perform proactive problem management.',
          'requirement_description': 'Collect and analyze operational data (especially incident and change records) to '
                                     'identify emerging trends that may indicate problems. Log problem records to enable '
                                     'assessment.',
          'subchapter': 'DSS03: Managed Problems'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.01: Define the business continuity policy, objectives and scope.',
          'requirement_description': 'Define business continuity policy and scope, aligned with enterprise and stakeholder '
                                     'objectives, to improve business resilience.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.02: Maintain business resilience.',
          'requirement_description': 'Evaluate business resilience options and choose a cost-effective and viable strategy '
                                     'that will ensure enterprise continuity, disaster recovery and incident response in the '
                                     'face of a disaster or other major incident or disruption.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.03: Develop and implement a business continuity response.',
          'requirement_description': 'Develop a business continuity plan (BCP) and disaster recovery plan (DRP) based on the '
                                     'strategy. Document all procedures necessary for the enterprise to continue critical '
                                     'activities in the event of an incident.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.04: Exercise, test and review the business continuity plan (BCP) and disaster response '
                             'plan (DRP).',
          'requirement_description': 'Test continuity on a regular basis to exercise plans against predetermined outcomes, '
                                     'uphold business resilience and allow innovative solutions to be developed.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.05: Review, maintain and improve the continuity plans.',
          'requirement_description': 'Conduct a management review of the continuity capability at regular intervals to ensure '
                                     'its continued suitability, adequacy and effectiveness. Manage changes to the plans in '
                                     'accordance with the change control process to ensure that continuity plans are kept up '
                                     'to date and continually reflect actual business requirements.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.06: Conduct continuity plan training.',
          'requirement_description': 'Provide all concerned internal and external parties with regular training sessions '
                                     'regarding procedures and their roles and responsibilities in case of disruption.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.07: Manage backup arrangements.',
          'requirement_description': 'Maintain availability of business-critical information.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS04.08: Conduct post-resumption review.',
          'requirement_description': 'Assess the adequacy of the business continuity plan (BCP) and disaster response plan '
                                     '(DRP) following successful resumption of business processes and services after a '
                                     'disruption.',
          'subchapter': 'DSS04: Managed Continuity'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.01: Protect against malicious software.',
          'requirement_description': 'Implement and maintain preventive, detective and corrective measures (especially '
                                     'up-to-date security patches and virus control) across the enterprise to protect '
                                     'information systems and technology from malicious software (e.g., malware, ransomware, '
                                     'viruses, worms, spyware, spam).',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.02: Manage network and connectivity security.',
          'requirement_description': 'Use security measures and related management procedures to protect information over all '
                                     'methods of connectivity.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.03: Manage endpoint security.',
          'requirement_description': 'Ensure that endpoints (e.g., laptop, desktop, server, and other mobile and network '
                                     'devices or software) are secured at a level that is equal to or greater than the defined '
                                     'security and privacy requirements for the information processed, stored or transmitted.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.04: Manage user identity and logical access.',
          'requirement_description': 'Ensure that all users have information access rights in accordance with the business '
                                     "unit's privacy policy and business requirements. Coordinate with business units that "
                                     'manage their own access rights within business processes.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.05: Manage physical access to I&T assets.',
          'requirement_description': 'Define and implement procedures (including emergency procedures) to grant, limit and '
                                     'revoke access to premises, buildings and areas, according to business need. Access to '
                                     'premises, buildings and areas should be justified, authorized, logged and monitored. '
                                     'This requirement applies to all persons entering the premises, including staff, '
                                     'temporary staff, clients, vendors, visitors or any other third party.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.06: Manage sensitive documents and output devices.',
          'requirement_description': 'Establish appropriate physical safeguards, accounting practices and inventory management '
                                     'regarding sensitive I&T assets, such as special forms, negotiable instruments, '
                                     'special-purpose printers or security tokens.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS05.07: Manage vulnerabilities and monitor the infrastructure for security-related events.',
          'requirement_description': 'Using a portfolio of tools and technologies (e.g., intrusion detection tools), manage '
                                     'vulnerabilities and monitor the infrastructure for unauthorized access. Ensure that '
                                     'security tools, technologies and detection are integrated with general event monitoring '
                                     'and incident management.',
          'subchapter': 'DSS05: Managed Security Services'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.01: Align control activities embedded in business processes with enterprise objectives.',
          'requirement_description': 'Continually assess and monitor the execution of business process activities and related '
                                     'controls (based on enterprise risk), to ensure that processing controls align with '
                                     'business needs.',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.02: Control the processing of information.',
          'requirement_description': 'Operate the execution of the business process activities and related controls, based on '
                                     'enterprise risk. Ensure that information processing is valid, complete, accurate, timely '
                                     'and secure (i.e., reflects legitimate and authorized business use).',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.03: Manage roles, responsibilities, access privileges and levels of authority.',
          'requirement_description': 'Manage business roles, responsibilities, levels of authority and segregation of duties '
                                     'needed to support the business process objectives. Authorize access to all information '
                                     'assets related to business information processes, including those under the custody of '
                                     'the business, IT and third parties. This ensures that the business knows where the data '
                                     'are and who is handling data on its behalf.',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.04: Manage errors and exceptions.',
          'requirement_description': 'Manage business process exceptions and errors and facilitate remediation, executing '
                                     'defined corrective actions and escalating as necessary. This treatment of exceptions and '
                                     'errors provides assurance of the accuracy and integrity of the business information '
                                     'process.',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.05: Ensure traceability and accountability for information events.',
          'requirement_description': 'Ensure that business information can be traced to an originating business event and '
                                     'associated with accountable parties. This discoverability provides assurance that '
                                     'business information is reliable and has been processed in accordance with defined '
                                     'objectives.',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'DSS: Deliver, Service and Support',
          'conformity_questions': [],
          'objective_title': 'DSS06.06: Secure information assets.',
          'requirement_description': 'Secure information assets accessible by the business through approved methods, including '
                                     'information in electronic form (e.g., portable media devices, user applications and '
                                     'storage devices, or other methods that create new assets in any form), information in '
                                     'physical form (e.g., source documents or output reports) and information during transit. '
                                     'This benefits the business by providing end-to-end safeguarding of information.',
          'subchapter': 'DSS06: Managed Business Process Controls'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA01.01: Establish a monitoring approach.',
          'requirement_description': 'Engage with stakeholders to establish and maintain a monitoring approach to define the '
                                     'objectives, scope and method for measuring business solution and service delivery and '
                                     'contribution to enterprise objectives. Integrate this approach with the corporate '
                                     'performance management system.',
          'subchapter': 'MEA01: Managed Performance and Conformance Monitoring'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA01.02: Set performance and conformance targets.',
          'requirement_description': 'Work with stakeholders to define, periodically review, update and approve performance '
                                     'and conformance targets within the performance measurement system.',
          'subchapter': 'MEA01: Managed Performance and Conformance Monitoring'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA01.03: Collect and process performance and conformance data.',
          'requirement_description': 'Collect and process timely and accurate data aligned with enterprise approaches.',
          'subchapter': 'MEA01: Managed Performance and Conformance Monitoring'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA01.04: Analyze and report performance.',
          'requirement_description': 'Periodically review and report performance against targets. Use a method that provides a '
                                     'succinct all-around view of I&T performance and fits within the enterprise monitoring '
                                     'system.',
          'subchapter': 'MEA01: Managed Performance and Conformance Monitoring'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA01.05: Ensure the implementation of corrective actions.',
          'requirement_description': 'Assist stakeholders in identifying, initiating and tracking corrective actions to '
                                     'address anomalies.',
          'subchapter': 'MEA01: Managed Performance and Conformance Monitoring'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA02.01: Monitor internal controls.',
          'requirement_description': 'Continuously monitor, benchmark and improve the I&T control environment and control '
                                     'framework to meet organizational objectives.',
          'subchapter': 'MEA02: Managed System of Internal Control'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA02.02: Review effectiveness of business process controls.',
          'requirement_description': 'Review the operation of controls, including monitoring and test evidence, to ensure that '
                                     'controls within business processes operate effectively. Include activities to maintain '
                                     'evidence of the effective operation of controls through mechanisms such as periodic '
                                     'testing, continuous monitoring, independent assessments, command and control centers, '
                                     'and network operation centers. This evidence assures the enterprise that controls meet '
                                     'requirements related to business, regulatory and social responsibilities.',
          'subchapter': 'MEA02: Managed System of Internal Control'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA02.03: Perform control self-assessments.',
          'requirement_description': 'Encourage management and process owners to improve controls proactively through a '
                                     'continuing program of self-assessment that evaluates the completeness and effectiveness '
                                     'of management?s control over processes, policies and contracts.',
          'subchapter': 'MEA02: Managed System of Internal Control'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA02.04: Identify and report control deficiencies.',
          'requirement_description': 'Identify control deficiencies and analyze and identify their underlying root causes. '
                                     'Escalate control deficiencies and report to stakeholders.',
          'subchapter': 'MEA02: Managed System of Internal Control'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA03.01: Identify external compliance requirements.',
          'requirement_description': 'On a continuous basis, monitor changes in local and international laws, regulations and '
                                     'other external requirements and identify mandates for compliance from an I&T '
                                     'perspective.',
          'subchapter': 'MEA03: Managed Compliance With External Requirements'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA03.02: Optimize response to external requirements.',
          'requirement_description': 'Review and adjust policies, principles, standards, procedures and methodologies to '
                                     'ensure that legal, regulatory and contractual requirements are addressed and '
                                     'communicated. Consider adopting and adapting industry standards, codes of good practice, '
                                     'and good practice guidance.',
          'subchapter': 'MEA03: Managed Compliance With External Requirements'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA03.03: Confirm external compliance.',
          'requirement_description': 'Confirm compliance of policies, principles, standards, procedures and methodologies with '
                                     'legal, regulatory and contractual requirements.',
          'subchapter': 'MEA03: Managed Compliance With External Requirements'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA03.04: Obtain assurance of external compliance.',
          'requirement_description': 'Obtain and report assurance of compliance and adherence with policies, principles, '
                                     'standards, procedures and methodologies. Confirm that corrective actions to address '
                                     'compliance gaps are closed in a timely manner.',
          'subchapter': 'MEA03: Managed Compliance With External Requirements'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.01: Ensure that assurance providers are independent and qualified.',
          'requirement_description': 'Ensure that the entities performing assurance are independent from the function, groups '
                                     'or organizations in scope. The entities performing assurance should demonstrate an '
                                     'appropriate attitude and appearance, competence in the skills and knowledge necessary to '
                                     'perform assurance, and adherence to codes of ethics and professional standards.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.02: Develop risk-based planning of assurance initiatives.',
          'requirement_description': 'Determine assurance objectives based on assessments of the internal and external '
                                     'environment and context, the risk of not achieving enterprise goals, and the '
                                     'opportunities associated achievement of the same goals.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.03: Determine the objectives of the assurance initiative.',
          'requirement_description': 'Define and agree with all stakeholders on the objectives of the assurance initiative.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.04: Define the scope of the assurance initiative.',
          'requirement_description': 'Define and agree with all stakeholders on the scope of the assurance initiative, based '
                                     'on the assurance objectives.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.05: Define the work program for the assurance initiative.',
          'requirement_description': 'Define a detailed work program for the assurance initiative, structured according to the '
                                     'management objectives and governance components in scope.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.06: Execute the assurance initiative, focusing on design effectiveness.',
          'requirement_description': 'Execute the planned assurance initiative. Validate and confirm the design of the '
                                     'internal controls in place. Additionally, and specifically in internal audit '
                                     'assignments, consider the cost-effectiveness of the governance component design.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.07: Execute the assurance initiative, focusing on operating effectiveness.',
          'requirement_description': 'Execute the planned assurance initiative. Test whether the internal controls in place '
                                     'are appropriate and sufficient. Test the outcome of the key management objectives in '
                                     'scope of the assurance initiative.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.08: Report and follow up on the assurance initiative.',
          'requirement_description': 'Provide positive assurance opinions, where appropriate, and recommendations for '
                                     'improvement relating to identified operational performance, external compliance and '
                                     'internal control weaknesses.',
          'subchapter': 'MEA04: Managed Assurance'},
         {'chapter_title': 'MEA: Monitor, Evaluate and Assess',
          'conformity_questions': [],
          'objective_title': 'MEA04.09: Follow up on recommendations and actions.',
          'requirement_description': 'Agree on, follow up and implement the identified recommendations for improvement. ',
          'subchapter': 'MEA04: Managed Assurance'}]
