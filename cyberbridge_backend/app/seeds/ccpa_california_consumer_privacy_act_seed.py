# app/seeds/ccpa_california_consumer_privacy_act_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class CcpaCaliforniaConsumerPrivacyActSeed(BaseSeed):
    """Seed CCPA (California Consumer Privacy Act) framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating CCPA (California Consumer Privacy Act) framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create CCPA (California Consumer Privacy Act) Framework
        ccpa_california_consumer_privacy_act_framework, created = self.get_or_create(
            models.Framework,
            {"name": "CCPA (California Consumer Privacy Act)", "organisation_id": default_org.id},
            {
                "name": "CCPA (California Consumer Privacy Act)",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("CCPA framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == ccpa_california_consumer_privacy_act_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == ccpa_california_consumer_privacy_act_framework.id
            ).all()

            logger.info(f"Found existing CCPA framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            return {
                "framework": ccpa_california_consumer_privacy_act_framework,
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
                description="CCPA (California Consumer Privacy Act) conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=ccpa_california_consumer_privacy_act_framework.id,
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
                        "framework_id": ccpa_california_consumer_privacy_act_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": ccpa_california_consumer_privacy_act_framework.id
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

        logger.info(f"Created CCPA (California Consumer Privacy Act) framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": ccpa_california_consumer_privacy_act_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return []

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'Article 1: General Provisions (999.300 - 999.301)',
          'conformity_questions': [],
          'objective_title': '999.300a: Title and Scope',
          'requirement_description': '(a) This Chapter shall be known as the California Consumer Privacy Act Regulations. It '
                                     'may be cited as such and will be referred to in this Chapter as these regulations." '
                                     'These regulations govern compliance with the California Consumer Privacy Act and do not '
                                     'limit any other rights that consumers may have. (b) A violation of these regulations '
                                     'shall constitute a violation of the CCPA and be subject to the remedies provided for '
                                     'therein."',
          'subchapter': 'Section 999.300: Title and Scope'},
         {'chapter_title': 'Article 1: General Provisions (999.300 - 999.301)',
          'conformity_questions': [],
          'objective_title': '999.301a: Definitions',
          'requirement_description': 'In addition to the definitions set forth in Civil Code section 1798.140, for purposes of '
                                     'these regulations: (a) Affirmative authorization" means an action that demonstrates the '
                                     'intentional decision by the consumer to opt-in to the sale of personal information. '
                                     'Within the context of a parent or guardian acting on behalf of a consumer under 13 years '
                                     'of age it means that the parent or guardian has provided consent to the sale of the '
                                     "consumer's personal information in accordance with the methods set forth in section "
                                     '999.330. For consumers 13 years of age and older\t it is demonstrated through a two-step '
                                     'process whereby the consumer shall first\t clearly request to opt-in and then second" '
                                     'separately confirm their choice to opt-in. (b) ""Attorney General"" means the California '
                                     'Attorney General or any officer or employee of the California Department of Justice '
                                     'acting under the authority of the California Attorney General.(c) ""Authorized agent"" '
                                     'means a natural person or a business entity registered with the Secretary of State to '
                                     'conduct business in California that a consumer has authorized to act on their behalf '
                                     'subject to the requirements set forth in section 999.326. (d) ""Categories of sources"" '
                                     'means types or groupings of persons or entities from which a business collects personal '
                                     'information about consumers"\t described with enough particularity to provide consumers '
                                     'with a meaningful understanding of the type of person or entity. They may include the '
                                     'consumer directly\t advertising networks\t internet service providers\t data analytics '
                                     'providers\t government entities\t operating systems and platforms\t social networks\t '
                                     'and data brokers.(e) "Categories of third parties" means types or groupings of third '
                                     'parties with whom the business shares personal information\t described with enough '
                                     'particularity to provide consumers with a meaningful understanding of the type of third '
                                     'party. They may include advertising networks\t internet service providers\t data '
                                     'analytics providers\t government entities\t operating systems and platforms\t social '
                                     'networks\t and data brokers.(f) "CCPA" means the California Consumer Privacy Act of '
                                     '2018\t Civil Code sections 1798.100 et seq.(g) "COPPA" means the Children\'s Online '
                                     'Privacy Protection Act\t 15 U.S.C. sections 6501 to 6508 and 16 Code of Federal '
                                     'Regulations part 312.5.(h) "Employment benefits" means retirement\t health\t and other '
                                     'benefit programs\t services\t or products to which consumers and their dependents or '
                                     "their beneficiaries receive access through the consumer's employer.(i) "
                                     '"Employment-related information" means personal information that is collected by the '
                                     'business about a natural person for the reasons identified in Civil Code section '
                                     '1798.145\t subdivision (h)(1). The collection of employment-related information\t '
                                     'including for the purpose of administering employment benefits\t shall be considered a '
                                     'business purpose.(j) "Financial incentive" means a program\t benefit\t or other '
                                     'offering\t including payments to consumers\t related to the collection\t deletion\t or '
                                     'sale of personal information. (k) "Household" means a person or group of people who: (1) '
                                     'reside at the same address\t (2) share a common device or the same service provided by a '
                                     'business\t and (3) are identified by the business as sharing the same group account or '
                                     'unique identifier. (l) "Notice at collection" means the notice given by a business to a '
                                     'consumer at or before the point at which a business collects personal information from '
                                     'the consumer as required by Civil Code section 1798.100\t subdivision (b)\t and '
                                     'specified in these regulations. (m) "Notice of right to opt-out" means the notice given '
                                     'by a business informing consumers of their right to opt-out of the sale of their '
                                     'personal information as required by Civil Code sections 1798.120 and 1798.135 and '
                                     'specified in these regulations. (n) "Notice of financial incentive" means the notice '
                                     'given by a business explaining each financial incentive or price or service difference '
                                     'as required by Civil Code section 1798.125\t subdivision (b)\t and specified in these '
                                     'regulations. (o) "Price or service difference" means (1) any difference in the price or '
                                     'rate charged for any goods or services to any consumer related to the collection\t '
                                     'retention\t or sale of personal information\t including through the use of discounts\t '
                                     'financial payments\t or other benefits or penalties; or (2) any difference in the level '
                                     'or quality of any goods or services offered to any consumer related to the collection\t '
                                     'retention\t or sale of personal information\t including the denial of goods or services '
                                     'to the consumer. (p) "Privacy policy\t as referred to in Civil Code section 1798.130, '
                                     'subdivision (a)(5), means the statement that a business shall make available to '
                                     "consumers describing the business's practices, both online and offline, regarding the "
                                     'collection, use, disclosure, and sale of personal information, and of the rights of '
                                     'consumers regarding their own personal information. (q) Request to delete" means a '
                                     'consumer request that a business delete personal information about the consumer that the '
                                     'business has collected from the consumer\t pursuant to Civil Code section 1798.105. (r) '
                                     '"Request to know" means a consumer request that a business disclose personal information '
                                     'that it has collected about the consumer pursuant to Civil Code sections 1798.100\t'
                                     '1798.11\t or 1798.115. It includes a request for any or all of the following: (1) '
                                     'Specific pieces of personal information that a business has collected about the '
                                     'consumer; (2) Categories of personal information it has collected about the consumer; '
                                     '(3) Categories of sources from which the personal information is collected; (4) '
                                     'Categories of personal information that the business sold or disclosed for a business '
                                     'purpose about the consumer; (5) Categories of third parties to whom the personal '
                                     'information was sold or disclosed for a business purpose; and (6) The business or '
                                     'commercial purpose for collecting or selling personal information. (s) "Request to '
                                     'opt-in" means the affirmative authorization that the business may sell personal '
                                     'information about the consumer by a parent or guardian of a consumer less than 13 years '
                                     'of age\t by a consumer at least 13 and less than 16 years of age\t or by a consumer who '
                                     'had previously opted out of the sale of their personal information. (t) "Request to '
                                     'opt-out" means a consumer request that a business not sell the consumer\'s personal '
                                     'information to third parties\t pursuant to Civil Code section 1798.120\t subdivision '
                                     '(a). (u) "Signed" means that the written attestation\t declaration\t or permission has '
                                     'either been physically signed or provided electronically in accordance with the Uniform '
                                     'Electronic Transactions Act\t Civil Code section 1633.1 et seq. (v) "Third-party '
                                     'identity verification service" means a security process offered by an independent third '
                                     'party that verifies the identity of the consumer making a request to the business. '
                                     'Third-party identity verification services are subject to the requirements set forth in '
                                     'Article 4 regarding requests to know and requests to delete. (w) "Value of the '
                                     'consumer\'s data" means the value provided to the business by the consumer\'s data as '
                                     'calculated under section 999.337. (x) "Verify" means to determine that the consumer '
                                     'making a request to know or request to delete is the consumer about whom the business '
                                     'has collected information\t or if that consumer is less than 13 years of age\t the '
                                     'consumer\'s parent or legal guardian."',
          'subchapter': 'Section 999.301: Definitions'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.304(a): Every business that must comply with the CCPA and these regulations shall provide a '
                             'privacy policy in accordance with the CCPA and section 999.308.',
          'requirement_description': '(a) Every business that must comply with the CCPA and these regulations shall provide a '
                                     'privacy policy in accordance with the CCPA and section 999.308.',
          'subchapter': 'Section 999.304: Overview of Required Notices'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.304(b): A business that collects personal information from a consumer shall provide a notice '
                             'at collection in accordance with the CCPA and section 999.305.',
          'requirement_description': '(b) A business that collects personal information from a consumer shall provide a notice '
                                     'at collection in accordance with the CCPA and section 999.305.',
          'subchapter': 'Section 999.304: Overview of Required Notices'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.304(c): A business that sells personal information shall provide a notice of right to '
                             'opt-out in accordance with the CCPA and section 999.306.',
          'requirement_description': '(c) A business that sells personal information shall provide a notice of right to '
                                     'opt-out in accordance with the CCPA and section 999.306.',
          'subchapter': 'Section 999.304: Overview of Required Notices'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.304(d): A business that offers a financial incentive or price or service difference shall '
                             'provide a notice of financial incentive in accordance with the CCPA and section 999.307.',
          'requirement_description': '(d) A business that offers a financial incentive or price or service difference shall '
                                     'provide a notice of financial incentive in accordance with the CCPA and section 999.307.',
          'subchapter': 'Section 999.304: Overview of Required Notices'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305 (a): Purpose and General Principles',
          'requirement_description': '\n'
                                     '(a) Purpose and General Principles \n'
                                     '(1) The purpose of the notice at collection is to provide consumers with timely notice, '
                                     'at or before the point of collection, about the categories of personal information to be '
                                     'collected from them and the purposes for which the personal information will be used. \n'
                                     '(2) The notice at collection shall be designed and presented in a way that is easy to '
                                     'read and understandable to consumers. The notice shall: a. Use plain, straightforward '
                                     "language and avoid technical or legal jargon. b. Use a format that draws the consumer's "
                                     'attention to the notice and makes the notice readable, including on smaller screens, if '
                                     'applicable. c. Be available in the languages in which the business in its ordinary '
                                     'course provides contracts, disclaimers, sale announcements, and other information to '
                                     'consumers in California. d. Be reasonably accessible to consumers with disabilities. For '
                                     'notices provided online, the business shall follow generally recognized industry '
                                     'standards, such as the Web Content Accessibility Guidelines, version 2.1 of June 5, '
                                     '2018, from the World Wide Web Consortium, incorporated herein by reference. In other '
                                     'contexts, the business shall provide information on how a consumer with a disability may '
                                     'access the notice in an alternative format. \n'
                                     '(3) The notice at collection shall be made readily available where consumers will '
                                     'encounter it at or before the point of collection of any personal information. '
                                     "Illustrative examples follow: a. When a business collects consumers' personal "
                                     'information online, it may post a conspicuous link to the notice on the introductory '
                                     "page of the business's website and on all webpages where personal information is "
                                     'collected. b. When a business collects personal information through a mobile '
                                     "application, it may provide a link to the notice on the mobile application's download "
                                     "page and within the application, such as through the application's settings menu. c. "
                                     "When a business collects consumers' personal information offline, it may include the "
                                     'notice on printed forms that collect personal information, provide the consumer with a '
                                     'paper version of the notice, or post prominent signage directing consumers to where the '
                                     'notice can be found online. d. When a business collects personal information over the '
                                     'telephone or in person, it may provide the notice orally. \n'
                                     "(4) When a business collects personal information from a consumer's mobile device for a "
                                     'purpose that the consumer would not reasonably expect, it shall provide a just-in-time '
                                     'notice containing a summary of the categories of personal information being collected '
                                     'and a link to the full notice at collection. For example, if the business offers a '
                                     'flashlight application and the application collects geolocation information, the '
                                     'business shall provide a just-in-time notice, such as through a pop-up window when the '
                                     'consumer opens the application, that contains the information required by this '
                                     'subsection. \n'
                                     '(5) A business shall not collect categories of personal information other than those '
                                     'disclosed in the notice at collection. If the business intends to collect additional '
                                     'categories of personal information, the business shall provide a new notice at '
                                     'collection. \n'
                                     '(6) If a business does not give the notice at collection to the consumer at or before '
                                     'the point of collection of their personal information, the business shall not collect '
                                     'personal information from the consumer.',
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(b): Notice at collection inclusions',
          'requirement_description': '\n'
                                     '(b) A business shall include the following in its notice at collection: \n'
                                     '(1) A list of the categories of personal information about consumers to be collected. '
                                     'Each category of personal information shall be written in a manner that provides '
                                     'consumers a meaningful understanding of the information being collected. \n'
                                     '(2) The business or commercial purpose(s) for which the categories of personal '
                                     'information will be used. \n'
                                     '(3) If the business sells personal information, the link titled ??Do Not Sell My '
                                     'Personal Information?@required by section 999.315, subsection (a), or in the case of '
                                     'offline notices, where the webpage can be found online. \n'
                                     "(4) A link to the business's privacy policy, or in the case of offline notices, where "
                                     'the privacy policy can be found online.',
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(c): If a business collects personal information from a consumer online, the notice at '
                             "collection may be given to the consumer by providing a link to the section of the business's "
                             'privacy policy that contains the information required in subsection .',
          'requirement_description': '(c) If a business collects personal information from a consumer online, the notice at '
                                     'collection may be given to the consumer by providing a link to the section of the '
                                     "business's privacy policy that contains the information required in subsection (b).",
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(d): A business that does not collect personal information directly from the consumer '
                             'does not need to provide a notice at collection to the consumer if it does not sell the '
                             "consumer's personal information.",
          'requirement_description': '(d) A business that does not collect personal information directly from the consumer '
                                     'does not need to provide a notice at collection to the consumer if it does not sell the '
                                     "consumer's personal information.",
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(e): A data broker registered with the Attorney General pursuant to Civil Code section '
                             '1798.99.80 et seq. does not need to provide a notice at collection to the consumer if it has '
                             'included in its registration submission a link to its online privacy policy that includes '
                             'instructions on how a consumer can submit a request to opt-out.',
          'requirement_description': '(e) A data broker registered with the Attorney General pursuant to Civil Code section '
                                     '1798.99.80 et seq. does not need to provide a notice at collection to the consumer if it '
                                     'has included in its registration submission a link to its online privacy policy that '
                                     'includes instructions on how a consumer can submit a request to opt-out.',
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(f): A business collecting employment-related information shall comply with the '
                             'provisions of section 999.305 except with regard to the following: (1) The notice at collection '
                             'of employment-related information does not need to include the link or web address to the link '
                             "titled  'Do Not Sell My Personal Information '. (2) The notice at collection of "
                             "employment-related information is not required to provide a link to the business's privacy "
                             'policy.',
          'requirement_description': '\n'
                                     '(f) A business collecting employment-related information shall comply with the '
                                     'provisions of section 999.305 except with regard to the following: \n'
                                     '(1) The notice at collection of employment-related information does not need to include '
                                     'the link or web address to the link titled ??Do Not Sell My Personal Information??. \n'
                                     '(2) The notice at collection of employment-related information is not required to '
                                     "provide a link to the business's privacy policy.",
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.305(g): Subsection  shall become inoperative on January 1, 2021, unless the CCPA is amended '
                             'otherwise.',
          'requirement_description': '(g) Subsection (f) shall become inoperative on January 1, 2021, unless the CCPA is '
                                     'amended otherwise.',
          'subchapter': 'Section 999.305: Notice at Collection of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(a): Purpose and General Principles',
          'requirement_description': '\n'
                                     '(a) Purpose and General Principles \n'
                                     '(1) The purpose of the notice of right to opt-out is to inform consumers of their right '
                                     'to direct a business that sells their personal information to stop selling their '
                                     'personal information.\n'
                                     '(2) The notice of right to opt-out shall be designed and presented in a way that is easy '
                                     'to read and understandable to consumers. The notice shall: a. Use plain, straightforward '
                                     "language and avoid technical or legal jargon. b. Use a format that draws the consumer's "
                                     'attention to the notice and makes the notice readable, including on smaller screens, if '
                                     'applicable. c. Be available in the languages in which the business in its ordinary '
                                     'course provides contracts, disclaimers, sale announcements, and other information to '
                                     'consumers in California. d. Be reasonably accessible to consumers with disabilities. For '
                                     'notices provided online, the business shall follow generally recognized industry '
                                     'standards, such as the Web Content Accessibility Guidelines, version 2.1 of June 5, '
                                     '2018, from the World Wide Web Consortium, incorporated herein by reference. In other '
                                     'contexts, the business shall provide information on how a consumer with a disability may '
                                     'access the notice in an alternative format.',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(b): A business that sells the personal information of consumers shall provide the notice '
                             'of right to opt-out to consumers.',
          'requirement_description': '(b) A business that sells the personal information of consumers shall provide the notice '
                                     'of right to opt-out to consumers as follows: (1) A business shall post the notice of '
                                     'right to opt-out on the Internet webpage to which the consumer is directed after '
                                     "clicking on the  'Do Not Sell My Personal Information?  link on the website homepage or "
                                     'the download or landing page of a mobile application. In addition, a business that '
                                     'collects personal information through a mobile application may provide a link to the '
                                     "notice within the application, such as through the application's settings menu. The "
                                     'notice shall include the information specified in subsection (c) or link to the section '
                                     "of the business's privacy policy that contains the same information. (2) A business that "
                                     'does not operate a website shall establish, document, and comply with another method by '
                                     'which it informs consumers of their right to opt-out. That method shall comply with the '
                                     'requirements set forth in subsection (a)(2).',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(c): Notice of right to opt-out',
          'requirement_description': '\n'
                                     '(c) A business shall include the following in its notice of right to opt-out: \n'
                                     "(1) A description of the consumer's right to opt-out of the sale of their personal "
                                     'information by the business; \n'
                                     '(2) The interactive form by which the consumer can submit their request to opt-out '
                                     'online, as required by section 999.315, subsection (a), or if the business does not '
                                     'operate a website, the offline method by which the consumer can submit their request to '
                                     'opt-out; and \n'
                                     '(3) Instructions for any other method by which the consumer may submit their request to '
                                     'opt-out.',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(d): A business does not need to provide a notice of right to opt-out if: (1) It does not '
                             'sell personal information; and (2) It states in its privacy policy that it does not sell '
                             'personal information.',
          'requirement_description': '\n'
                                     '(d) A business does not need to provide a notice of right to opt-out if: \n'
                                     '(1) It does not sell personal information; and \n'
                                     '(2) It states in its privacy policy that it does not sell personal information.',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(e): A business shall not sell the personal information it collected during the time the '
                             'business did not have a notice of right to opt-out posted unless it obtains the affirmative '
                             'authorization of the consumer.',
          'requirement_description': '(e) A business shall not sell the personal information it collected during the time the '
                                     'business did not have a notice of right to opt-out posted unless it obtains the '
                                     'affirmative authorization of the consumer.',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.306(f): Opt-Out Icon',
          'requirement_description': '\n'
                                     '(f) Opt-out Icon. \n'
                                     '(1)The following opt-out icon may be used in addition to posting the notice of right to '
                                     'opt-out, but not in lieu of any requirement to post the notice of right to opt-out or a '
                                     '"Do Not Sell My Personal Information" link as required by Civil Code section 1798.135 '
                                     'and these regulations.\n'
                                     '(2)The icon shall be approximately the same size as any other icons used by the business '
                                     'on its webpage.',
          'subchapter': 'Section 999.306: Notice of Right to Opt-Out of Sale of Personal Information'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.307(a): Purpose and General Principles',
          'requirement_description': '\n'
                                     '(a) Purpose and General Principles \n'
                                     '(1) The purpose of the notice of financial incentive is to explain to the consumer the '
                                     'material terms of a financial incentive or price or service difference the business is '
                                     'offering so that the consumer may make an informed decision about whether to '
                                     'participate. A business that does not offer a financial incentive or price or service '
                                     'difference is not required to provide a notice of financial incentive. \n'
                                     '(2) The notice of financial incentive shall be designed and presented in a way that is '
                                     'easy to read and understandable to consumers. The notice shall: a. Use plain, '
                                     'straightforward language and avoid technical or legal jargon. b. Use a format that draws '
                                     "the consumer's attention to the notice and makes the notice readable, including on "
                                     'smaller screens, if applicable. c. Be available in the languages in which the business '
                                     'in its ordinary course provides contracts, disclaimers, sale announcements, and other '
                                     'information to consumers in California. d. Be reasonably accessible to consumers with '
                                     'disabilities. For notices provided online, the business shall follow generally '
                                     'recognized industry standards, such as the Web Content Accessibility Guidelines, version '
                                     '2.1 of June 5, 2018, from the World Wide Web Consortium, incorporated herein by '
                                     'reference. In other contexts, the business shall provide information on how a consumer '
                                     'with a disability may access the notice in an alternative format. e. Be readily '
                                     'available where consumers will encounter it before opting-in to the financial incentive '
                                     'or price or service difference. \n'
                                     '(3) If the business offers the financial incentive or price or service difference '
                                     "online, the notice may be given by providing a link to the section of a business's "
                                     'privacy policy that contains the information required in subsection (b).',
          'subchapter': 'Section 999.307: Notice of Financial Incentive'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.307(b): Notice of financial incentive',
          'requirement_description': '\n'
                                     '(b) A business shall include the following in its notice of financial incentive: \n'
                                     '(1) A succinct summary of the financial incentive or price or service difference '
                                     'offered; \n'
                                     '(2) A description of the material terms of the financial incentive or price or service '
                                     'difference, including the categories of personal information that are implicated by the '
                                     "financial incentive or price or service difference and the value of the consumer's "
                                     'data; \n'
                                     '(3) How the consumer can opt-in to the financial incentive or price or service '
                                     'difference; \n'
                                     "(4) A statement of the consumer's right to withdraw from the financial incentive at any "
                                     'time and how the consumer may exercise that right; and\n'
                                     '(5) An explanation of how the financial incentive or price or service difference is '
                                     "reasonably related to the value of the consumer's data, including a. A good-faith "
                                     "estimate of the value of the consumer's data that forms the basis for offering the "
                                     'financial incentive or price or service difference; and b. A description of the method '
                                     "the business used to calculate the value of the consumer's data.",
          'subchapter': 'Section 999.307: Notice of Financial Incentive'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.308(a): Purpose and General Principles',
          'requirement_description': '\n'
                                     '(a) Purpose and General Principles \n'
                                     '(1) The purpose of the privacy policy is to provide consumers with a comprehensive '
                                     "description of a business's online and offline practices regarding the collection, use, "
                                     'disclosure, and sale of personal information and of the rights of consumers regarding '
                                     'their personal information. \n'
                                     '(2) The privacy policy shall be designed and presented in a way that is easy to read and '
                                     'understandable to consumers. The policy shall: a. Use plain, straightforward language '
                                     'and avoid technical or legal jargon. b. Use a format that makes the policy readable, '
                                     'including on smaller screens, if applicable. c. Be available in the languages in which '
                                     'the business in its ordinary course provides contracts, disclaimers, sale announcements, '
                                     'and other information to consumers in California. d. Be reasonably accessible to '
                                     'consumers with disabilities. For notices provided online, the business shall follow '
                                     'generally recognized industry standards, such as the Web Content Accessibility '
                                     'Guidelines, version 2.1 of June 5, 2018, from the World Wide Web Consortium, '
                                     'incorporated herein by reference. In other contexts, the business shall provide '
                                     'information on how a consumer with a disability may access the policy in an alternative '
                                     'format. e. Be available in a format that allows a consumer to print it out as a '
                                     'document.',
          'subchapter': 'Section 999.308: Privacy Policy'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.308(b): The privacy policy shall be posted online through a conspicuous link using the word '
                             "'privacy' on the business's website homepage or on the download or landing page of a mobile "
                             'application.',
          'requirement_description': '(b) The privacy policy shall be posted online through a conspicuous link using the word  '
                                     "'privacy?  on the business's website homepage or on the download or landing page of a "
                                     "mobile application. If the business has a California-specific description of consumers' "
                                     'privacy rights on its website, then the privacy policy shall be included in that '
                                     'description. A business that does not operate a website shall make the privacy policy '
                                     'conspicuously available to consumers. A mobile application may include a link to the '
                                     "privacy policy in the application's settings menu.",
          'subchapter': 'Section 999.308: Privacy Policy'},
         {'chapter_title': 'Article 2: Notices to Consumers (999.304 - 999.308)',
          'conformity_questions': [],
          'objective_title': '999.308(c): Privacy policy information',
          'requirement_description': '\n'
                                     '(b) The privacy policy shall be posted online through a conspicuous link using the word '
                                     "??privacy?@on the business's website homepage or on the download or landing page of a "
                                     "mobile application. If the business has a California-specific description of consumers' "
                                     'privacy rights on its website, then the privacy policy shall be included in that '
                                     'description. A business that does not operate a website shall make the privacy policy '
                                     'conspicuously available to consumers. A mobile application may include a link to the '
                                     "privacy policy in the application's settings menu.",
          'subchapter': 'Section 999.308: Privacy Policy'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.312(a): A business that operates exclusively online and has a direct relationship with a '
                             'consumer from whom it collects personal information shall only be required to provide an email '
                             'address for submitting requests to know. All other businesses shall provide two or more '
                             'designated methods for submitting requests to know, including, at a minimum, a toll-free '
                             'telephone number. Other acceptable methods for submitting these requests include, but are not '
                             'limited to, a designated email address, a form submitted in person, and a form submitted through '
                             'the mail.',
          'requirement_description': '(a) A business that operates exclusively online and has a direct relationship with a '
                                     'consumer from whom it collects personal information shall only be required to provide an '
                                     'email address for submitting requests to know. All other businesses shall provide two or '
                                     'more designated methods for submitting requests to know, including, at a minimum, a '
                                     'toll-free telephone number. Other acceptable methods for submitting these requests '
                                     'include, but are not limited to, a designated email address, a form submitted in person, '
                                     'and a form submitted through the mail.',
          'subchapter': 'Section 999.312: Methods for Submitting Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.312(b): A business shall provide two or more designated methods for submitting requests to '
                             'delete...',
          'requirement_description': '(b) A business shall provide two or more designated methods for submitting requests to '
                                     'delete. Acceptable methods for submitting these requests include, but are not limited '
                                     "to, a toll-free phone number, a link or form available online through a business's "
                                     'website, a designated email address, a form submitted in person, and a form submitted '
                                     'through the mail.',
          'subchapter': 'Section 999.312: Methods for Submitting Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.312(c): A business shall consider the methods by which it primarily interacts with consumers '
                             'when determining which methods to provide for submitting requests to know and requests to '
                             'delete...',
          'requirement_description': '(c) A business shall consider the methods by which it primarily interacts with consumers '
                                     'when determining which methods to provide for submitting requests to know and requests '
                                     'to delete. If the business interacts with consumers in person, the business shall '
                                     'consider providing an in-person method such as a printed form the consumer can directly '
                                     'submit or send by mail, a tablet or computer portal that allows the consumer to complete '
                                     'and submit an online form, or a telephone with which the consumer can call the '
                                     "business's toll-free number.",
          'subchapter': 'Section 999.312: Methods for Submitting Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.312(d): A business may use a two-step process for online requests to delete where the '
                             'consumer must first, submit the request to delete and then second, separately confirm that they '
                             'want their personal information deleted.',
          'requirement_description': '(d) A business may use a two-step process for online requests to delete where the '
                                     'consumer must first, submit the request to delete and then second, separately confirm '
                                     'that they want their personal information deleted.',
          'subchapter': 'Section 999.312: Methods for Submitting Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.312(e): If a consumer submits a request in a manner that is not one of the designated '
                             'methods of submission, or is deficient in some manner unrelated to the verification process, the '
                             'business shall either: (1) Treat the request as if it had been submitted in accordance with the '
                             "business's designated manner, or (2) Provide the consumer with information on how to submit the "
                             'request or remedy any deficiencies with the request, if applicable.',
          'requirement_description': '\n'
                                     '(e) If a consumer submits a request in a manner that is not one of the designated '
                                     'methods of submission, or is deficient in some manner unrelated to the verification '
                                     'process, the business shall either: \n'
                                     "(1) Treat the request as if it had been submitted in accordance with the business's "
                                     'designated manner, or \n'
                                     '(2) Provide the consumer with information on how to submit the request or remedy any '
                                     'deficiencies with the request, if applicable.',
          'subchapter': 'Section 999.312: Methods for Submitting Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.313(a): Upon receiving a request to know or a request to delete, a business shall confirm '
                             'receipt of the request within 10 business days and provide information about how the business '
                             'will process the request...',
          'requirement_description': '(a) Upon receiving a request to know or a request to delete, a business shall confirm '
                                     'receipt of the request within 10 business days and provide information about how the '
                                     'business will process the request. The information provided shall describe in general '
                                     "the business's verification process and when the consumer should expect a response, "
                                     'except in instances where the business has already granted or denied the request. The '
                                     'confirmation may be given in the same manner in which the request was received. For '
                                     'example, if the request is made over the phone, the confirmation may be given orally '
                                     'during the phone call.',
          'subchapter': 'Section 999.313: Responding to Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.313(b): Businesses shall respond to requests to know and requests to delete within 45 '
                             'calendar days.',
          'requirement_description': '(b) Businesses shall respond to requests to know and requests to delete within 45 '
                                     'calendar days. The 45-day period will begin on the day that the business receives the '
                                     'request, regardless of time required to verify the request. If the business cannot '
                                     'verify the consumer within the 45-day time period, the business may deny the request. If '
                                     'necessary, businesses may take up to an additional 45 calendar days to respond to the '
                                     "consumer's request, for a maximum total of 90 calendar days from the day the request is "
                                     'received, provided that the business provides the consumer with notice and an '
                                     'explanation of the reason that the business will take more than 45 days to respond to '
                                     'the request.',
          'subchapter': 'Section 999.313: Responding to Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.313(c): Responding to Requests to Know',
          'requirement_description': '\n'
                                     '(c) Responding to Requests to Know. \n'
                                     '(1) For requests that seek the disclosure of specific pieces of information about the '
                                     'consumer, if a business cannot verify the identity of the person making the request '
                                     'pursuant to the regulations set forth in Article 4, the business shall not disclose any '
                                     'specific pieces of personal information to the requestor and shall inform the requestor '
                                     'that it cannot verify their identity. If the request is denied in whole or in part, the '
                                     "business shall also evaluate the consumer's request as if it is seeking the disclosure "
                                     'of categories of personal information about the consumer pursuant to subsection '
                                     '(c)(2). \n'
                                     '(2) For requests that seek the disclosure of categories of personal information about '
                                     'the consumer, if a business cannot verify the identity of the person making the request '
                                     'pursuant to the regulations set forth in Article 4, the business may deny the request to '
                                     'disclose the categories and other information requested and shall inform the requestor '
                                     'that it cannot verify their identity. If the request is denied in whole or in part, the '
                                     'business shall provide or direct the consumer to its general business practices '
                                     'regarding the collection, maintenance, and sale of personal information set forth in its '
                                     'privacy policy. \n'
                                     '(3) In responding to a request to know, a business is not required to search for '
                                     'personal information if all of the following conditions are met: a. The business does '
                                     'not maintain the personal information in a searchable or reasonably accessible format; '
                                     'b. The business maintains the personal information solely for legal or compliance '
                                     'purposes; c. The business does not sell the personal information and does not use it for '
                                     'any commercial purpose; and d. The business describes to the consumer the categories of '
                                     'records that may contain personal information that it did not search because it meets '
                                     'the conditions stated above. \n'
                                     "(4) A business shall not disclose in response to a request to know a consumer's Social "
                                     "Security number, driver's license number or other government-issued identification "
                                     'number, financial account number, any health insurance or medical identification number, '
                                     'an account password, security questions and answers, or unique biometric data generated '
                                     'from measurements or technical analysis of human characteristics. The business shall, '
                                     'however, inform the consumer with sufficient particularity that it has collected the '
                                     'type of information. For example, a business shall respond that it collects ??unique '
                                     'biometric data including a fingerprint scan?@without disclosing the actual fingerprint '
                                     'scan data. \n'
                                     "(5) If a business denies a consumer's verified request to know specific pieces of "
                                     'personal information, in whole or in part, because of a conflict with federal or state '
                                     'law, or an exception to the CCPA, the business shall inform the requestor and explain '
                                     'the basis for the denial, unless prohibited from doing so by law. If the request is '
                                     'denied only in part, the business shall disclose the other information sought by the '
                                     'consumer. \n'
                                     '(6) A business shall use reasonable security measures when transmitting personal '
                                     'information to the consumer. \n'
                                     '(7) If a business maintains a password-protected account with the consumer, it may '
                                     'comply with a request to know by using a secure self-service portal for consumers to '
                                     'access, view, and receive a portable copy of their personal information if the portal '
                                     'fully discloses the personal information that the consumer is entitled to under the CCPA '
                                     'and these regulations, uses reasonable data security controls, and complies with the '
                                     'verification requirements set forth in Article 4. (8) Unless otherwise specified by the '
                                     "business to cover a longer period of time, the 12-month period covered by a consumer's "
                                     'verifiable request to know referenced in Civil Code section 1798.130, subdivision '
                                     '(a)(2), shall run from the date the business receives the request, regardless of the '
                                     'time required to verify the request. \n'
                                     "(9) In responding to a consumer's verified request to know categories of personal "
                                     'information, categories of sources, and/or categories of third parties, a business shall '
                                     'provide an individualized response to the consumer as required by the CCPA. It shall not '
                                     "refer the consumer to the businesses' general practices outlined in its privacy policy "
                                     'unless its response would be the same for all consumers and the privacy policy discloses '
                                     'all the information that is otherwise required to be in a response to a request to know '
                                     'such categories. \n'
                                     '(10) In responding to a verified request to know categories of personal information, the '
                                     'business shall provide: a. The categories of personal information the business has '
                                     'collected about the consumer in the preceding 12 months; b. The categories of sources '
                                     'from which the personal information was collected; c. The business or commercial purpose '
                                     'for which it collected or sold the personal information; d. The categories of third '
                                     'parties with whom the business shares personal information; e. The categories of '
                                     'personal information that the business sold in the preceding 12 months, and for each '
                                     'category identified, the categories of third parties to whom it sold that particular '
                                     'category of personal information; and f. The categories of personal information that the '
                                     'business disclosed for a business purpose in the preceding 12 months, and for each '
                                     'category identified, the categories of third parties to whom it disclosed that '
                                     'particular category of personal information. \n'
                                     '(11) A business shall identify the categories of personal information, categories of '
                                     'sources of personal information, and categories of third parties to whom a business sold '
                                     'or disclosed personal information, in a manner that provides consumers a meaningful '
                                     'understanding of the categories listed.',
          'subchapter': 'Section 999.313: Responding to Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.313(d): Responding to Requests to Delete.',
          'requirement_description': '\n'
                                     '(d) Responding to Requests to Delete. \n'
                                     '(1) For requests to delete, if a business cannot verify the identity of the requestor '
                                     'pursuant to the regulations set forth in Article 4, the business may deny the request to '
                                     'delete. The business shall inform the requestor that their identity cannot be '
                                     'verified. \n'
                                     "(2) A business shall comply with a consumer's request to delete their personal "
                                     'information by: a. Permanently and completely erasing the personal information on its '
                                     'existing systems with the exception of archived or back-up systems; b. Deidentifying the '
                                     'personal information; or c. Aggregating the consumer information. \n'
                                     '(3) If a business stores any personal information on archived or backup systems, it may '
                                     "delay compliance with the consumer's request to delete, with respect to data stored on "
                                     'the archived or backup system, until the archived or backup system relating to that data '
                                     'is restored to an active system or next accessed or used for a sale, disclosure, or '
                                     'commercial purpose. \n'
                                     '(4) In responding to a request to delete, a business shall inform the consumer whether '
                                     "or not it has complied with the consumer's request. \n"
                                     "(5) If the business complies with the consumer's request, the business shall inform the "
                                     'consumer that it will maintain a record of the request as required by section 999.317, '
                                     'subsection (b). A business may retain a record of the request for the purpose of '
                                     "ensuring that the consumer's personal information remains deleted from the business's "
                                     'records. \n'
                                     "(6) In cases where a business denies a consumer's request to delete, the business shall "
                                     'do all of the following: a. Inform the consumer that it will not comply with the '
                                     "consumer's request and describe the basis for the denial, including any conflict with "
                                     'federal or state law, or exception to the CCPA, unless prohibited from doing so by law; '
                                     "b. Delete the consumer's personal information that is not subject to the exception; and "
                                     "c. Not use the consumer's personal information retained for any other purpose than "
                                     'provided for by that exception. \n'
                                     "(7) If a business that denies a consumer's request to delete sells personal information "
                                     'and the consumer has not already made a request to opt-out, the business shall ask the '
                                     'consumer if they would like to opt-out of the sale of their personal information and '
                                     'shall include either the contents of, or a link to, the notice of right to opt-out in '
                                     'accordance with section 999.306. \n'
                                     '(8) In responding to a request to delete, a business may present the consumer with the '
                                     'choice to delete select portions of their personal information only if a global option '
                                     'to delete all personal information is also offered and more prominently presented than '
                                     'the other choices.',
          'subchapter': 'Section 999.313: Responding to Requests to Know and Requests to Delete'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(a): A business that provides services to a person or organization that is not a '
                             "business, and that would otherwise meet the requirements and obligations of a  'service   "
                             "provider'  under the CCPA and these regulations, shall be deemed a service provider for purposes "
                             'of the CCPA and these regulations.',
          'requirement_description': '(a) A business that provides services to a person or organization that is not a '
                                     'business, and that would otherwise meet the requirements and obligations of a  '
                                     "'service   provider'  under the CCPA and these regulations, shall be deemed a service "
                                     'provider for purposes of the CCPA and these regulations.',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(b): To the extent that a business directs a second entity to collect personal '
                             "information directly from a consumer, or about a consumer, on the first business's behalf, and "
                             "the second entity would otherwise meet the requirements and obligations of a  'service   "
                             "provider'  under the CCPA and these regulations, the second entity shall be deemed a service "
                             'provider of the first business for purposes of the CCPA and these regulations.',
          'requirement_description': '(b) To the extent that a business directs a second entity to collect personal '
                                     "information directly from a consumer, or about a consumer, on the first business's "
                                     'behalf, and the second entity would otherwise meet the requirements and obligations of '
                                     "a  'service   provider'  under the CCPA and these regulations, the second entity shall "
                                     'be deemed a service provider of the first business for purposes of the CCPA and these '
                                     'regulations.',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(c): A service provider shall not retain, use, or disclose personal information obtained '
                             'in the course of providing services...',
          'requirement_description': '(c) A service provider shall not retain, use, or disclose personal information obtained '
                                     'in the course of providing services except: (1) To process or maintain personal '
                                     'information on behalf of the business that provided the personal information or directed '
                                     'the service provider to collect the personal information, and in compliance with the '
                                     'written contract for services required by the CCPA; (2) To retain and employ another '
                                     'service provider as a subcontractor, where the subcontractor meets the requirements for '
                                     'a service provider under the CCPA and these regulations; (3) For internal use by the '
                                     'service provider to build or improve the quality of its services, provided that the use '
                                     'does not include building or modifying household or consumer profiles to use in '
                                     'providing services to another business, or correcting or augmenting data acquired from '
                                     'another source; (4) To detect data security incidents or protect against fraudulent or '
                                     'illegal activity; or (5) For the purposes enumerated in Civil Code section 1798.145, '
                                     'subdivisions (a)(1) through (a)(4).',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(d): A service provider shall not sell data on behalf of a business when a consumer has '
                             'opted-out of the sale of their personal information with the business.',
          'requirement_description': '(d) A service provider shall not sell data on behalf of a business when a consumer has '
                                     'opted-out of the sale of their personal information with the business.',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(e): If a service provider receives a request to know or a request to delete from a '
                             'consumer, the service provider shall either act on behalf of the business in responding to the '
                             'request or inform the consumer that the request cannot be acted upon because the request has '
                             'been sent to a service provider.',
          'requirement_description': '(e) If a service provider receives a request to know or a request to delete from a '
                                     'consumer, the service provider shall either act on behalf of the business in responding '
                                     'to the request or inform the consumer that the request cannot be acted upon because the '
                                     'request has been sent to a service provider.',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.314(f): A service provider that is a business shall comply with the CCPA and these '
                             'regulations with regard to any personal information that it collects, maintains, or sells '
                             'outside of its role as a service provider.',
          'requirement_description': '(f) A service provider that is a business shall comply with the CCPA and these '
                                     'regulations with regard to any personal information that it collects, maintains, or '
                                     'sells outside of its role as a service provider.',
          'subchapter': 'Section 999.314: Service Providers'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(a): A business shall provide two or more designated methods for submitting requests to '
                             'opt-out...',
          'requirement_description': '(a) A business shall provide two or more designated methods for submitting requests to '
                                     'opt-out, including an interactive form accessible via a clear and conspicuous link '
                                     "titled  'Do Not Sell My Personal Information,?  on the business's website or mobile "
                                     'application. Other acceptable methods for submitting these requests include, but are not '
                                     'limited to, a toll-free phone number, a designated email address, a form submitted in '
                                     'person, a form submitted through the mail, and user-enabled global privacy controls, '
                                     'such as a browser plug-in or privacy setting, device setting, or other mechanism, that '
                                     "communicate or signal the consumer's choice to opt-out of the sale of their personal "
                                     'information.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(b): A business shall consider the methods by which it interacts with consumers, the '
                             'manner in which the business sells personal information to third parties, available technology, '
                             'and ease of use by the consumer when determining which methods consumers may use to submit '
                             'requests to opt-out. At least one method offered shall reflect the manner in which the business '
                             'primarily interacts with the consumer.',
          'requirement_description': '(b) A business shall consider the methods by which it interacts with consumers, the '
                                     'manner in which the business sells personal information to third parties, available '
                                     'technology, and ease of use by the consumer when determining which methods consumers may '
                                     'use to submit requests to opt-out. At least one method offered shall reflect the manner '
                                     'in which the business primarily interacts with the consumer.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(c): If a business collects personal information from consumers online, the business '
                             'shall treat user-enabled global privacy controls, such as a browser plug-in or privacy setting, '
                             "device setting, or other mechanism, that communicate or signal the consumer's choice to opt-out "
                             'of the sale of their personal information as a valid request submitted pursuant to Civil Code '
                             'section 1798.120 for that browser or device, or, if known, for the consumer...',
          'requirement_description': '(c) If a business collects personal information from consumers online, the business '
                                     'shall treat user-enabled global privacy controls, such as a browser plug-in or privacy '
                                     "setting, device setting, or other mechanism, that communicate or signal the consumer's "
                                     'choice to opt-out of the sale of their personal information as a valid request submitted '
                                     'pursuant to Civil Code section 1798.120 for that browser or device, or, if known, for '
                                     'the consumer. (1) Any privacy control developed in accordance with these regulations '
                                     'shall clearly communicate or signal that a consumer intends to opt-out of the sale of '
                                     "personal information. (2) If a global privacy control conflicts with a consumer's "
                                     "existing business-specific privacy setting or their participation in a business's "
                                     'financial incentive program, the business shall respect the global privacy control but '
                                     'may notify the consumer of the conflict and give the consumer the choice to confirm the '
                                     'business-specific privacy setting or participation in the financial incentive program.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(d): In responding to a request to opt-out, a business may present the consumer with the '
                             'choice to opt-out of sale for certain uses of personal information as long as a global option to '
                             'opt-out of the sale of all personal information is more prominently presented than the other '
                             'choices.',
          'requirement_description': '(d) In responding to a request to opt-out, a business may present the consumer with the '
                                     'choice to opt-out of sale for certain uses of personal information as long as a global '
                                     'option to opt-out of the sale of all personal information is more prominently presented '
                                     'than the other choices.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(e): A business shall comply with a request to opt-out as soon as feasibly possible, but '
                             'no later than 15 business days from the date the business receives the request...',
          'requirement_description': '(e) A business shall comply with a request to opt-out as soon as feasibly possible, but '
                                     'no later than 15 business days from the date the business receives the request. If a '
                                     "business sells a consumer's personal information to any third parties after the consumer "
                                     'submits their request but before the business complies with that request, it shall '
                                     'notify those third parties that the consumer has exercised their right to opt-out and '
                                     "shall direct those third parties not to sell that consumer's information.",
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(f): A consumer may use an authorized agent to submit a request to opt-out on the '
                             "consumer's behalf if the consumer provides the authorized agent written permission signed by the "
                             'consumer.',
          'requirement_description': '(f) A consumer may use an authorized agent to submit a request to opt-out on the '
                                     "consumer's behalf if the consumer provides the authorized agent written permission "
                                     'signed by the consumer. A business may deny a request from an authorized agent if the '
                                     "agent cannot provide to the business the consumer's signed permission demonstrating that "
                                     "they have been authorized by the consumer to act on the consumer's behalf. User-enabled "
                                     'global privacy controls, such as a browser plug-in or privacy setting, device setting, '
                                     "or other mechanism, that communicate or signal the consumer's choice to opt-out of the "
                                     'sale of their personal information shall be considered a request directly from the '
                                     'consumer, not through an authorized agent.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.315(g): A request to opt-out need not be a verifiable consumer request. If a business, '
                             'however, has a good-faith, reasonable, and documented belief that a request to opt-out is '
                             'fraudulent, the business may deny the request. The business shall inform the requestor that it '
                             'will not comply with the request and shall provide an explanation why it believes the request is '
                             'fraudulent.',
          'requirement_description': '(g) A request to opt-out need not be a verifiable consumer request. If a business, '
                                     'however, has a good-faith, reasonable, and documented belief that a request to opt-out '
                                     'is fraudulent, the business may deny the request. The business shall inform the '
                                     'requestor that it will not comply with the request and shall provide an explanation why '
                                     'it believes the request is fraudulent.',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': "999.315(h): A business's methods for submitting request to opt-out shall be easy for consumers "
                             'to execute and shall require minimal steps to allow the consumer to opt-out',
          'requirement_description': "(h) A business's methods for submitting request to opt-out shall be easy for consumers "
                                     'to execute and shall require minimal steps to allow the consumer to opt-out. A business '
                                     'shall not use a method that is designed with the purpose or has the substantial effect '
                                     "of subverting or impairing a consumer's choice to opt-out. Illustrative examples "
                                     'follow:\n'
                                     "(1)The business's process for submitting a request to opt-out shall not require more "
                                     "steps than that business's process for a consumer to opt-in to the sale of personal "
                                     'information after having previously opted out. The number of steps for submitting a '
                                     'request to opt-out is measured from when the consumer clicks on the Do Not Sell My '
                                     'Personal Information" link to completion of the request. The number of steps for '
                                     'submitting a request to opt-in to the sale of personal information is measured from the '
                                     'first indication by the consumer to the business of their interest to opt-out in '
                                     'completion of the request.\n'
                                     '(2)A business shall not use confusing language\t such as double-negatives (e.g."Don\'t '
                                     'Not Sell My Personal Information")when providing consumers the choice to opt-out.\n'
                                     '(3)Except as permitted by these regulations  a business shall not require consumers to '
                                     'click through or listen to reasons why they should not submit a request to opt-out '
                                     'before confirming their request.\n'
                                     "(4)The business's process for submitting a request to opt-out shall not require the "
                                     'consumer to provide personal information that is not necessary to implement the '
                                     'request.\n'
                                     '(5)Upon clicking the "Do Not Sell My Personal Information" link\t the business shall not '
                                     'require the consumer to search or scroll through the text of a privacy policy or similar '
                                     'document or webpage to locate the mechanism for submitting a request to opt-out."',
          'subchapter': 'Section 999.315: Requests to Opt-Out'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.316(a): Requests to opt-in to the sale of personal information shall use a two-step opt-in '
                             'process whereby the consumer shall first, clearly request to opt-in and then second, separately '
                             'confirm their choice to opt-in.',
          'requirement_description': '(a) Requests to opt-in to the sale of personal information shall use a two-step opt-in '
                                     'process whereby the consumer shall first, clearly request to opt-in and then second, '
                                     'separately confirm their choice to opt-in.',
          'subchapter': 'Section 999.316: Requests to Opt-in After Opting-Out of the Sale of Personal Information'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.316(b): If a consumer who has opted-out of the sale of their personal information initiates '
                             'a transaction or attempts to use a product or service that requires the sale of their personal '
                             'information, a business may inform the consumer that the transaction, product, or service '
                             'requires the sale of their personal information and provide instructions on how the consumer can '
                             'opt-in.',
          'requirement_description': '(b) If a consumer who has opted-out of the sale of their personal information initiates '
                                     'a transaction or attempts to use a product or service that requires the sale of their '
                                     'personal information, a business may inform the consumer that the transaction, product, '
                                     'or service requires the sale of their personal information and provide instructions on '
                                     'how the consumer can opt-in.',
          'subchapter': 'Section 999.316: Requests to Opt-in After Opting-Out of the Sale of Personal Information'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': "999.317(a): All individuals responsible for handling consumer inquiries about the business's "
                             "privacy practices or the business's compliance with the CCPA shall be informed of all of the "
                             'requirements in the CCPA and these regulations and how to direct consumers to exercise their '
                             'rights under the CCPA and these regulations.',
          'requirement_description': "(a) All individuals responsible for handling consumer inquiries about the business's "
                                     "privacy practices or the business's compliance with the CCPA shall be informed of all of "
                                     'the requirements in the CCPA and these regulations and how to direct consumers to '
                                     'exercise their rights under the CCPA and these regulations.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(b): A business shall maintain records of consumer requests made pursuant to the CCPA and '
                             'how it responded to the requests for at least 24 months. The business shall implement and '
                             'maintain reasonable security procedures and practices in maintaining these records.',
          'requirement_description': '(b) A business shall maintain records of consumer requests made pursuant to the CCPA and '
                                     'how it responded to the requests for at least 24 months. The business shall implement '
                                     'and maintain reasonable security procedures and practices in maintaining these records.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(c): The records may be maintained in a ticket or log format provided that the ticket or '
                             'log includes the date of request, nature of request, manner in which the request was made, the '
                             "date of the business's response, the nature of the response, and the basis for the denial of the "
                             'request if the request is denied in whole or in part.',
          'requirement_description': '(c) The records may be maintained in a ticket or log format provided that the ticket or '
                                     'log includes the date of request, nature of request, manner in which the request was '
                                     "made, the date of the business's response, the nature of the response, and the basis for "
                                     'the denial of the request if the request is denied in whole or in part.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': "999.317(d): A business's maintenance of the information required by this section, where that "
                             'information is not used for any other purpose, does not taken alone violate the CCPA or these '
                             'regulations.',
          'requirement_description': "(d) A business's maintenance of the information required by this section, where that "
                                     'information is not used for any other purpose, does not taken alone violate the CCPA or '
                                     'these regulations.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(e): Information maintained for record-keeping purposes shall not be used for any other '
                             'purpose except as reasonably necessary for the business to review and modify its processes for '
                             'compliance with the CCPA and these regulations. Information maintained for record-keeping '
                             'purposes shall not be shared with any third party except as necessary to comply with a legal '
                             'obligation.',
          'requirement_description': '(e) Information maintained for record-keeping purposes shall not be used for any other '
                                     'purpose except as reasonably necessary for the business to review and modify its '
                                     'processes for compliance with the CCPA and these regulations. Information maintained for '
                                     'record-keeping purposes shall not be shared with any third party except as necessary to '
                                     'comply with a legal obligation.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(f): Other than as required by subsection , a business is not required to retain personal '
                             'information solely for the purpose of fulfilling a consumer request made under the CCPA.',
          'requirement_description': '(f) Other than as required by subsection (b), a business is not required to retain '
                                     'personal information solely for the purpose of fulfilling a consumer request made under '
                                     'the CCPA.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(g): A business that knows or reasonably should know that it, alone or in combination, '
                             "buys, receives for the business's commercial purposes, sells, or shares for commercial purposes "
                             'the personal information of 10,000,000 or more consumers in a calendar year...',
          'requirement_description': '(g) A business that knows or reasonably should know that it, alone or in combination, '
                                     "buys, receives for the business's commercial purposes, sells, or shares for commercial "
                                     'purposes the personal information of 10,000,000 or more consumers in a calendar year '
                                     'shall: (1) Compile the following metrics for the previous calendar year: a. The number '
                                     'of requests to know that the business received, complied with in whole or in part, and '
                                     'denied; b. The number of requests to delete that the business received, complied with in '
                                     'whole or in part, and denied; c. The number of requests to opt-out that the business '
                                     'received, complied with in whole or in part, and denied; and  d. The median or mean '
                                     'number of days within which the business substantively responded to requests to know, '
                                     'requests to delete, and requests to opt-out. (2) Disclose, by July 1 of every calendar '
                                     'year, the information compiled in subsection (g)(1) within their privacy policy or '
                                     'posted on their website and accessible from a link included in their privacy policy. a. '
                                     'In its disclosure pursuant to subsection (g)(2), a business may choose to disclose the '
                                     'number of requests that it denied in whole or in part because the request was not '
                                     'verifiable, was not made by a consumer, called for information exempt from disclosure, '
                                     'or was denied on other grounds. (3) Establish, document, and comply with a training '
                                     'policy to ensure that all individuals responsible for handling consumer requests made '
                                     "under the CCPA or the business's compliance with the CCPA are informed of all the "
                                     'requirements in these regulations and the CCPA. ',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.317(h): A business may choose to compile and disclose the information required by subsection '
                             '(1) for requests received from all individuals, rather than requests received from consumers. '
                             'The business shall state whether it has done so in its disclosure and shall, upon request, '
                             'compile and provide to the Attorney General the information required by subsection (1) for '
                             'requests received from consumers.',
          'requirement_description': '(h) A business may choose to compile and disclose the information required by subsection '
                                     '(g)(1) for requests received from all individuals, rather than requests received from '
                                     'consumers. The business shall state whether it has done so in its disclosure and shall, '
                                     'upon request, compile and provide to the Attorney General the information required by '
                                     'subsection (g)(1) for requests received from consumers.',
          'subchapter': 'Section 999.317: Training; Record-Keeping'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.318(a): Where a household does not have a password-protected account with a business, a '
                             'business shall not comply with a request to know specific pieces of personal information about '
                             'the household or a request to delete household personal information unless all of the following '
                             'conditions are satisfied...',
          'requirement_description': '(a) Where a household does not have a password-protected account with a business, a '
                                     'business shall not comply with a request to know specific pieces of personal information '
                                     'about the household or a request to delete household personal information unless all of '
                                     'the following conditions are satisfied: (1) All consumers of the household jointly '
                                     'request to know specific pieces of information for the household or the deletion of '
                                     'household personal information; (2) The business individually verifies all the members '
                                     'of the household subject to the verification requirements set forth in section 999.325; '
                                     'and (3) The business verifies that each member making the request is currently a member '
                                     'of the household.',
          'subchapter': 'Section 999.318: Requests to Know or Delete Household Information'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.318(b): Where a consumer has a password-protected account with a business that collects '
                             'personal information about a household, the business may process requests to know and requests '
                             "to delete relating to household information through the business's existing business practices "
                             'and in compliance with these regulations.',
          'requirement_description': '(b) Where a consumer has a password-protected account with a business that collects '
                                     'personal information about a household, the business may process requests to know and '
                                     "requests to delete relating to household information through the business's existing "
                                     'business practices and in compliance with these regulations.',
          'subchapter': 'Section 999.318: Requests to Know or Delete Household Information'},
         {'chapter_title': 'Article 3: Business Practices for Handling Consumer Requests (999.312 - 999.318)',
          'conformity_questions': [],
          'objective_title': '999.318(c): If a member of a household is a consumer under the age of 13, a business must obtain '
                             'verifiable parental consent before complying with a request to know specific pieces of '
                             'information for the household or the deletion of household personal information pursuant to the '
                             'parental consent provisions in section 999.330.',
          'requirement_description': '(c) If a member of a household is a consumer under the age of 13, a business must obtain '
                                     'verifiable parental consent before complying with a request to know specific pieces of '
                                     'information for the household or the deletion of household personal information pursuant '
                                     'to the parental consent provisions in section 999.330.',
          'subchapter': 'Section 999.318: Requests to Know or Delete Household Information'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.323(a): A business shall establish, document, and comply with a reasonable method for '
                             'verifying that the person making a request to know or a request to delete is the consumer about '
                             'whom the business has collected information.',
          'requirement_description': '(a) A business shall establish, document, and comply with a reasonable method for '
                                     'verifying that the person making a request to know or a request to delete is the '
                                     'consumer about whom the business has collected information.',
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.323(b): In determining the method by which the business will verify the consumer's identity, "
                             'the business shall...',
          'requirement_description': '\n'
                                     "(b) In determining the method by which the business will verify the consumer's identity, "
                                     'the business shall: \n'
                                     '(1) Whenever feasible, match the identifying information provided by the consumer to the '
                                     'personal information of the consumer already maintained by the business, or use a '
                                     'third-party identity verification service that complies with this section. \n'
                                     '(2) Avoid collecting the types of personal information identified in Civil Code section '
                                     '1798.81.5, subdivision (d), unless necessary for the purpose of verifying the '
                                     'consumer. \n'
                                     '(3) Consider the following factors: a. The type, sensitivity, and value of the personal '
                                     'information collected and maintained about the consumer. Sensitive or valuable personal '
                                     'information shall warrant a more stringent verification process. The types of personal '
                                     'information identified in Civil Code section 1798.81.5, subdivision (d), shall be '
                                     'considered presumptively sensitive; b. The risk of harm to the consumer posed by any '
                                     'unauthorized access or deletion. A greater risk of harm to the consumer by unauthorized '
                                     'access or deletion shall warrant a more stringent verification process; c. The '
                                     'likelihood that fraudulent or malicious actors would seek the personal information. The '
                                     'higher the likelihood, the more stringent the verification process shall be; d. Whether '
                                     'the personal information to be provided by the consumer to verify their identity is '
                                     'sufficiently robust to protect against fraudulent requests or being spoofed or '
                                     'fabricated; e. The manner in which the business interacts with the consumer; and f. '
                                     'Available technology for verification.',
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.323(c): A business shall generally avoid requesting additional information from the consumer '
                             'for purposes of verification...',
          'requirement_description': '(c) A business shall generally avoid requesting additional information from the consumer '
                                     'for purposes of verification. If, however, the business cannot verify the identity of '
                                     'the consumer from the information already maintained by the business, the business may '
                                     'request additional information from the consumer, which shall only be used for the '
                                     'purposes of verifying the identity of the consumer seeking to exercise their rights '
                                     'under the CCPA, security, or fraud-prevention. The business shall delete any new '
                                     'personal information collected for the purposes of verification as soon as practical '
                                     "after processing the consumer's request, except as required to comply with section "
                                     '999.317.',
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.323(d): A business shall not require the consumer or the consumer's authorized agent to pay "
                             'a fee for the verification of their request to know or request to delete. For example, a '
                             'business may not require a consumer to provide a notarized affidavit to verify their identity '
                             'unless the business compensates the consumer for the cost of notarization.',
          'requirement_description': "(d) A business shall not require the consumer or the consumer's authorized agent to pay "
                                     'a fee for the verification of their request to know or request to delete. For example, a '
                                     'business may not require a consumer to provide a notarized affidavit to verify their '
                                     'identity unless the business compensates the consumer for the cost of notarization.',
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.323(e): A business shall implement reasonable security measures to detect fraudulent '
                             'identity-verification activity and prevent the unauthorized access to or deletion of a '
                             "consumer's personal information.",
          'requirement_description': '(e) A business shall implement reasonable security measures to detect fraudulent '
                                     'identity-verification activity and prevent the unauthorized access to or deletion of a '
                                     "consumer's personal information.",
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.323(f): If a business maintains consumer information that is deidentified, a business is not '
                             'obligated to provide or delete this information in response to a consumer request or to '
                             're-identify individual data to verify a consumer request.',
          'requirement_description': '(f) If a business maintains consumer information that is deidentified, a business is not '
                                     'obligated to provide or delete this information in response to a consumer request or to '
                                     're-identify individual data to verify a consumer request.',
          'subchapter': 'Section 999.323: General Rules Regarding Verification'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.324(a): If a business maintains a password-protected account with the consumer, the business '
                             "may verify the consumer's identity through the business's existing authentication practices for "
                             "the consumer's account, provided that the business follows the requirements in section 999.323. "
                             'The business shall also require a consumer to re-authenticate themself before disclosing or '
                             "deleting the consumer's data.",
          'requirement_description': '(a) If a business maintains a password-protected account with the consumer, the business '
                                     "may verify the consumer's identity through the business's existing authentication "
                                     "practices for the consumer's account, provided that the business follows the "
                                     'requirements in section 999.323. The business shall also require a consumer to '
                                     "re-authenticate themself before disclosing or deleting the consumer's data.",
          'subchapter': 'Section 999.324: Verification for Password-Protected Accounts'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.324(b): If a business suspects fraudulent or malicious activity on or from the '
                             "password-protected account, the business shall not comply with a consumer's request to know or "
                             'request to delete until further verification procedures determine that the consumer request is '
                             'authentic and the consumer making the request is the person about whom the business has '
                             'collected information. The business may use the procedures set forth in section 999.325 to '
                             'further verify the identity of the consumer.',
          'requirement_description': '(b) If a business suspects fraudulent or malicious activity on or from the '
                                     "password-protected account, the business shall not comply with a consumer's request to "
                                     'know or request to delete until further verification procedures determine that the '
                                     'consumer request is authentic and the consumer making the request is the person about '
                                     'whom the business has collected information. The business may use the procedures set '
                                     'forth in section 999.325 to further verify the identity of the consumer.',
          'subchapter': 'Section 999.324: Verification for Password-Protected Accounts'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.325(a): If a consumer does not have or cannot access a password-protected account with a '
                             'business, the business shall comply with this section, in addition to section 999.323.',
          'requirement_description': '(a) If a consumer does not have or cannot access a password-protected account with a '
                                     'business, the business shall comply with this section, in addition to section 999.323.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.325(b): A business's compliance with a request to know categories of personal information "
                             'requires that the business verify the identity of the consumer making the request to a '
                             'reasonable degree of certainty. A reasonable degree of certainty may include matching at least '
                             'two data points provided by the consumer with data points maintained by the business that it has '
                             'determined to be reliable for the purpose of verifying the consumer.',
          'requirement_description': "(b) A business's compliance with a request to know categories of personal information "
                                     'requires that the business verify the identity of the consumer making the request to a '
                                     'reasonable degree of certainty. A reasonable degree of certainty may include matching at '
                                     'least two data points provided by the consumer with data points maintained by the '
                                     'business that it has determined to be reliable for the purpose of verifying the '
                                     'consumer.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.325(c): A business's compliance with a request to know specific pieces of personal "
                             'information requires that the business verify the identity of the consumer making the request to '
                             'a reasonably high degree of certainty...',
          'requirement_description': "(c) A business's compliance with a request to know specific pieces of personal "
                                     'information requires that the business verify the identity of the consumer making the '
                                     'request to a reasonably high degree of certainty. A reasonably high degree of certainty '
                                     'may include matching at least three pieces of personal information provided by the '
                                     'consumer with personal information maintained by the business that it has determined to '
                                     'be reliable for the purpose of verifying the consumer together with a signed declaration '
                                     'under penalty of perjury that the requestor is the consumer whose personal information '
                                     'is the subject of the request. If a business uses this method for verification, the '
                                     'business shall maintain all signed declarations as part of its record-keeping '
                                     'obligations.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.325(d): A business's compliance with a request to delete may require that the business "
                             'verify the identity of the consumer to a reasonable or reasonably high degree of certainty '
                             'depending on the sensitivity of the personal information and the risk of harm to the consumer '
                             'posed by unauthorized deletion.',
          'requirement_description': "(d) A business's compliance with a request to delete may require that the business "
                                     'verify the identity of the consumer to a reasonable or reasonably high degree of '
                                     'certainty depending on the sensitivity of the personal information and the risk of harm '
                                     'to the consumer posed by unauthorized deletion. For example, the deletion of family '
                                     'photographs may require a reasonably high degree of certainty, while the deletion of '
                                     'browsing history may require only a reasonable degree of certainty. A business shall act '
                                     'in good faith when determining the appropriate standard to apply when verifying the '
                                     'consumer in accordance with these regulations.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.325(e): Illustrative examples',
          'requirement_description': '(e) Illustrative examples follow: (1) Example 1: If a business maintains personal '
                                     'information in a manner associated with a named actual person, the business may verify '
                                     'the consumer by requiring the consumer to provide evidence that matches the personal '
                                     'information maintained by the business. For example, if a retailer maintains a record of '
                                     'purchases made by a consumer, the business may require the consumer to identify items '
                                     'that they recently purchased from the store or the dollar amount of their most recent '
                                     'purchase to verify their identity to a reasonable degree of certainty. (2) Example 2: If '
                                     'a business maintains personal information in a manner that is not associated with a '
                                     'named actual person, the business may verify the consumer by requiring the consumer to '
                                     'demonstrate that they are the sole consumer associated with the personal information. '
                                     'For example, a business may have a mobile application that collects personal information '
                                     'about the consumer but does not require an account. The business may determine whether, '
                                     'based on the facts and considering the factors set forth in section 999.323, subsection '
                                     '(b)(3), it may reasonably verify a consumer by asking them to provide information that '
                                     'only the person who used the mobile application may know or by requiring the consumer to '
                                     'respond to a notification sent to their device.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.325(f): A business shall deny a request to know specific pieces of personal information if '
                             'it cannot verify the identity of the requestor pursuant to these regulations.',
          'requirement_description': '(f) A business shall deny a request to know specific pieces of personal information if '
                                     'it cannot verify the identity of the requestor pursuant to these regulations.',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.325(g): If there is no reasonable method by which a business can verify the identity of the '
                             'consumer to the degree of certainty required by this section, the business shall state so in '
                             'response to any request and explain why it has no reasonable method by which it can verify the '
                             'identity of the requestor...',
          'requirement_description': '(g) If there is no reasonable method by which a business can verify the identity of the '
                                     'consumer to the degree of certainty required by this section, the business shall state '
                                     'so in response to any request and explain why it has no reasonable method by which it '
                                     'can verify the identity of the requestor. If the business has no reasonable method by '
                                     'which it can verify any consumer, the business shall explain why it has no reasonable '
                                     'verification method in its privacy policy. The business shall evaluate and document '
                                     'whether a reasonable method can be established at least once every 12 months, in '
                                     'connection with the requirement to update the privacy policy set forth in Civil Code '
                                     'section 1798.130, subdivision (a)(5).',
          'subchapter': 'Section 999.325: Verification for Non-Accountholders'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.326(a): When a consumer uses an authorized agent to submit a request to know or a request to '
                             'delete, a business may require that the consumer do the following...',
          'requirement_description': '\n'
                                     '(a) When a consumer uses an authorized agent to submit a request to know or a request to '
                                     'delete, a business may require that the consumer do the following: \n'
                                     '(1) Provide the authorized agent signed permission to do so. \n'
                                     '(2) Verify their own identity directly with the business. \n'
                                     '(3) Directly confirm with the business that they provided the authorized agent '
                                     'permission to submit the request.',
          'subchapter': 'Section 999.326: Authorized Agent'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.326(b): Subsection  does not apply when a consumer has provided the authorized agent with '
                             'power of attorney pursuant to Probate Code sections 4121 to 4130.',
          'requirement_description': '(b) Subsection (a) does not apply when a consumer has provided the authorized agent with '
                                     'power of attorney pursuant to Probate Code sections 4121 to 4130.',
          'subchapter': 'Section 999.326: Authorized Agent'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': '999.326(c): An authorized agent shall implement and maintain reasonable security procedures and '
                             "practices to protect the consumer's information.",
          'requirement_description': '(c) An authorized agent shall implement and maintain reasonable security procedures and '
                                     "practices to protect the consumer's information.",
          'subchapter': 'Section 999.326: Authorized Agent'},
         {'chapter_title': 'Article 4: Verification of Requests (999.323 - 999.326)',
          'conformity_questions': [],
          'objective_title': "999.326(d): An authorized agent shall not use a consumer's personal information, or any "
                             'information collected from or about the consumer, for any purposes other than to fulfill the '
                             "consumer's requests, verification, or fraud prevention.",
          'requirement_description': "(d) An authorized agent shall not use a consumer's personal information, or any "
                                     'information collected from or about the consumer, for any purposes other than to fulfill '
                                     "the consumer's requests, verification, or fraud prevention.",
          'subchapter': 'Section 999.326: Authorized Agent'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.330(a): Process for Opting-In to Sale of Personal Information',
          'requirement_description': '\n'
                                     '(a) Process for Opting-In to Sale of Personal Information \n'
                                     '(1) A business that has actual knowledge that it sells the personal information of a '
                                     'consumer under the age of 13 shall establish, document, and comply with a reasonable '
                                     'method for determining that the person affirmatively authorizing the sale of the '
                                     'personal information about the child is the parent or guardian of that child. This '
                                     'affirmative authorization is in addition to any verifiable parental consent required '
                                     'under COPPA. \n'
                                     '(2) Methods that are reasonably calculated to ensure that the person providing consent '
                                     "is the child's parent or guardian include, but are not limited to: \n"
                                     '  a. Providing a consent form to be signed by the parent or guardian under penalty of '
                                     'perjury and returned to the business by postal mail, facsimile, or electronic scan;\n'
                                     '   b. Requiring a parent or guardian, in connection with a monetary transaction, to use '
                                     'a credit card, debit card, or other online payment system that provides notification of '
                                     'each discrete transaction to the primary account holder; \n'
                                     'c. Having a parent or guardian call a toll-free telephone number staffed by trained '
                                     'personnel; d. Having a parent or guardian connect to trained personnel via '
                                     'video-conference; \n'
                                     'e. Having a parent or guardian communicate in person with trained personnel; and f. '
                                     "Verifying a parent or guardian's identity by checking a form of government-issued "
                                     'identification against databases of such information, as long as the parent or '
                                     "guardian's identification is deleted by the business from its records promptly after "
                                     'such verification is complete.',
          'subchapter': 'Section 999.330: Consumers Under 13 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.330(b): When a business receives an affirmative authorization pursuant to subsection , the '
                             'business shall inform the parent or guardian of the right to opt-out and of the process for '
                             'doing so on behalf of their child pursuant to section 999.315.',
          'requirement_description': '(b) When a business receives an affirmative authorization pursuant to subsection (a), '
                                     'the business shall inform the parent or guardian of the right to opt-out and of the '
                                     'process for doing so on behalf of their child pursuant to section 999.315, subsections '
                                     '(a)-(f).',
          'subchapter': 'Section 999.330: Consumers Under 13 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.330(c): A business shall establish, document, and comply with a reasonable method, in '
                             'accordance with the methods set forth in subsection (2), for determining that a person '
                             'submitting a request to know or a request to delete the personal information of a child under '
                             'the age of 13 is the parent or guardian of that child.',
          'requirement_description': '(c) A business shall establish, document, and comply with a reasonable method, in '
                                     'accordance with the methods set forth in subsection (a)(2), for determining that a '
                                     'person submitting a request to know or a request to delete the personal information of a '
                                     'child under the age of 13 is the parent or guardian of that child.',
          'subchapter': 'Section 999.330: Consumers Under 13 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.331(a): A business that has actual knowledge that it sells the personal information of '
                             'consumers at least 13 years of age and less than 16 years of age shall establish, document, and '
                             'comply with a reasonable process for allowing such consumers to opt-in to the sale of their '
                             'personal information, pursuant to section 999.316.',
          'requirement_description': '(a) A business that has actual knowledge that it sells the personal information of '
                                     'consumers at least 13 years of age and less than 16 years of age shall establish, '
                                     'document, and comply with a reasonable process for allowing such consumers to opt-in to '
                                     'the sale of their personal information, pursuant to section 999.316.',
          'subchapter': 'Section 999.331: Consumers 13 to 15 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.331(b): When a business receives a request to opt-in to the sale of personal information '
                             'from a consumer at least 13 years of age and less than 16 years of age, the business shall '
                             'inform the consumer of the right to opt-out at a later date and of the process for doing so '
                             'pursuant to section 999.315.',
          'requirement_description': '(b) When a business receives a request to opt-in to the sale of personal information '
                                     'from a consumer at least 13 years of age and less than 16 years of age, the business '
                                     'shall inform the consumer of the right to opt-out at a later date and of the process for '
                                     'doing so pursuant to section 999.315.',
          'subchapter': 'Section 999.331: Consumers 13 to 15 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.332(a): A business subject to sections 999.330 and 999.331 shall include a description of '
                             'the processes set forth in those sections in its privacy policy.',
          'requirement_description': '(a) A business subject to sections 999.330 and 999.331 shall include a description of '
                                     'the processes set forth in those sections in its privacy policy.',
          'subchapter': 'Section 999.332: Notices to Consumers Under 16 Years of Age'},
         {'chapter_title': 'Article 5: Special Rules Regarding Consumers Under 16 Years of Age (999.330 - 999.332)',
          'conformity_questions': [],
          'objective_title': '999.332(b): A business that exclusively targets offers of goods or services directly to '
                             'consumers under 16 years of age and does not sell the personal information without the '
                             'affirmative authorization of consumers at least 13 years of age and less than 16 years of age, '
                             'or the affirmative authorization of their parent or guardian for consumers under 13 years of '
                             'age, is not required to provide the notice of right to opt-out.',
          'requirement_description': '(b) A business that exclusively targets offers of goods or services directly to '
                                     'consumers under 16 years of age and does not sell the personal information without the '
                                     'affirmative authorization of consumers at least 13 years of age and less than 16 years '
                                     'of age, or the affirmative authorization of their parent or guardian for consumers under '
                                     '13 years of age, is not required to provide the notice of right to opt-out.',
          'subchapter': 'Section 999.332: Notices to Consumers Under 16 Years of Age'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.336(a): A financial incentive or a price or service difference is discriminatory, and '
                             'therefore prohibited by Civil Code section 1798.125, if the business treats a consumer '
                             'differently because the consumer exercised a right conferred by the CCPA or these regulations.',
          'requirement_description': '(a) A financial incentive or a price or service difference is discriminatory, and '
                                     'therefore prohibited by Civil Code section 1798.125, if the business treats a consumer '
                                     'differently because the consumer exercised a right conferred by the CCPA or these '
                                     'regulations.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.336(b): A business may offer a financial incentive or price or service difference if it is '
                             "reasonably related to the value of the consumer's data. If a business is unable to calculate a "
                             "good-faith estimate of the value of the consumer's data or cannot show that the financial "
                             "incentive or price or service difference is reasonably related to the value of the consumer's "
                             'data, that business shall not offer the financial incentive or price or service difference.',
          'requirement_description': '(b) A business may offer a financial incentive or price or service difference if it is '
                                     "reasonably related to the value of the consumer's data. If a business is unable to "
                                     "calculate a good-faith estimate of the value of the consumer's data or cannot show that "
                                     'the financial incentive or price or service difference is reasonably related to the '
                                     "value of the consumer's data, that business shall not offer the financial incentive or "
                                     'price or service difference.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': "999.336(c): A business's denial of a consumer's request to know, request to delete, or request "
                             'to opt-out for reasons permitted by the CCPA or these regulations shall not be considered '
                             'discriminatory.',
          'requirement_description': "(c) A business's denial of a consumer's request to know, request to delete, or request "
                                     'to opt-out for reasons permitted by the CCPA or these regulations shall not be '
                                     'considered discriminatory.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.336(d): Illustrative examples',
          'requirement_description': '\n'
                                     '(d) Illustrative examples follow: \n'
                                     '(1) Example 1: A music streaming business offers a free service as well as a premium '
                                     'service that costs $5 per month. If only the consumers who pay for the music streaming '
                                     'service are allowed to opt-out of the sale of their personal information, then the '
                                     'practice is discriminatory, unless the $5-per-month payment is reasonably related to the '
                                     "value of the consumer's data to the business. \n"
                                     '(2) Example 2: A clothing business offers a loyalty program whereby customers receive a '
                                     '$5-off coupon by email after spending $100 with the business. A consumer submits a '
                                     'request to delete all personal information the business has collected about them but '
                                     'also informs the business that they want to continue to participate in the loyalty '
                                     'program. The business may deny their request to delete with regard to their email '
                                     'address and the amount the consumer has spent with the business because that information '
                                     'is necessary for the business to provide the loyalty program requested by the consumer '
                                     "and is reasonably anticipated within the context of the business's ongoing relationship "
                                     'with them pursuant to Civil Code section 1798.105, subdivision (d)(1). \n'
                                     '(3) Example 3: A grocery store offers a loyalty program whereby consumers receive '
                                     'coupons and special discounts when they provide their phone numbers. A consumer submits '
                                     'a request to opt-out of the sale of their personal information. The retailer complies '
                                     'with their request but no longer allows the consumer to participate in the loyalty '
                                     'program. This practice is discriminatory unless the grocery store can demonstrate that '
                                     'the value of the coupons and special discounts are reasonably related to the value of '
                                     "the consumer's data to the business. \n"
                                     '(4) Example 4: An online bookseller collects information about consumers, including '
                                     'their email addresses. It offers coupons to consumers through browser pop-up windows '
                                     "while the consumer uses the bookseller's website. A consumer submits a request to delete "
                                     'all personal information that the bookseller has collected about them, including their '
                                     'email address and their browsing and purchasing history. The bookseller complies with '
                                     "the request but stops providing the periodic coupons to the consumer. The bookseller's "
                                     'failure to provide coupons is discriminatory unless the value of the coupons is '
                                     "reasonably related to the value provided to the business by the consumer's data. The "
                                     "bookseller may not deny the consumer's request to delete with regard to the email "
                                     'address because the email address is not necessary to provide the coupons or reasonably '
                                     "aligned with the expectations of the consumer based on the consumer's relationship with "
                                     'the business.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.336(e): A business shall notify consumers of any financial incentive or price or service '
                             'difference subject to Civil Code section 1798.125 that it offers in accordance with section '
                             '999.307.',
          'requirement_description': '(e) A business shall notify consumers of any financial incentive or price or service '
                                     'difference subject to Civil Code section 1798.125 that it offers in accordance with '
                                     'section 999.307.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': "999.336(f): A business's charging of a reasonable fee pursuant to Civil Code section 1798.145, "
                             'subdivision (3), shall not be considered a financial incentive subject to these regulations.',
          'requirement_description': "(f) A business's charging of a reasonable fee pursuant to Civil Code section 1798.145, "
                                     'subdivision (i)(3), shall not be considered a financial incentive subject to these '
                                     'regulations.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.336(g): A price or service difference that is the direct result of compliance with a state '
                             'or federal law shall not be considered discriminatory.',
          'requirement_description': '(g) A price or service difference that is the direct result of compliance with a state '
                                     'or federal law shall not be considered discriminatory.',
          'subchapter': 'Section 999.336: Discriminatory Practices'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.337(a): A business offering a financial incentive or price or service difference subject to '
                             'Civil Code section 1798.125 shall use and document a reasonable and good faith method for '
                             "calculating the value of the consumer's data...",
          'requirement_description': '\n'
                                     '(a) A business offering a financial incentive or price or service difference subject to '
                                     'Civil Code section 1798.125 shall use and document a reasonable and good faith method '
                                     "for calculating the value of the consumer's data. The business shall consider one or "
                                     'more of the following: \n'
                                     '(1) The marginal value to the business of the sale, collection, or deletion of a '
                                     "consumer's data. \n"
                                     '(2) The average value to the business of the sale, collection, or deletion of a '
                                     "consumer's data. \n"
                                     '(3) The aggregate value to the business of the sale, collection, or deletion of '
                                     "consumers' data divided by the total number of consumers. \n"
                                     "(4) Revenue generated by the business from sale, collection, or retention of consumers' "
                                     'personal information. \n'
                                     "(5) Expenses related to the sale, collection, or retention of consumers' personal "
                                     'information. \n'
                                     '(6) Expenses related to the offer, provision, or imposition of any financial incentive '
                                     'or price or service difference. \n'
                                     "(7) Profit generated by the business from sale, collection, or retention of consumers' "
                                     'personal information. \n'
                                     '(8) Any other practical and reasonably reliable method of calculation used in good '
                                     'faith.',
          'subchapter': 'Section 999.337: Calculating the Value of Consumer Data'},
         {'chapter_title': 'Article 6: Non-Discrimination (999.336 - 999.337)',
          'conformity_questions': [],
          'objective_title': '999.337(b): For the purpose of calculating the value of consumer data, a business may consider '
                             'the value to the business of the data of all natural persons in the United States and not just '
                             'consumers.',
          'requirement_description': '\n'
                                     '(b) For the purpose of calculating the value of consumer data, a business may consider '
                                     'the value to the business of the data of all natural persons in the United States and '
                                     'not just consumers.',
          'subchapter': 'Section 999.337: Calculating the Value of Consumer Data'}]
