# import requests
# import pathlib
# from utils.file_helpers import read_json
# import argparse
# from multiprocessing import Pool, cpu_count, freeze_support
# import random
# from bs4 import BeautifulSoup
# import re
# from datetime import datetime
# from reportlab.lib.pagesizes import letter, A4
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.lib import colors
# from reportlab.lib.enums import TA_CENTER, TA_LEFT
# from reportlab.platypus import Image as RLImage
# import io
# import base64
# import matplotlib
# matplotlib.use('Agg')  # Use non-interactive backend for server environments
# import matplotlib.pyplot as plt
# from collections import Counter

# # Structured keyword categories
# KEYWORD_CATEGORIES = {
#     "password": {
#         "main": "password",
#         "subcategories": [
#             "password", "passwd", "pwd", "pass", "passphrase", "secret", "pin", "code",
#             "p4ssw0rd", "p@ssw0rd", "p@$$word", "p455w0rd", "authentication", "auth",
#             "login", "signin", "credential", "token", "hash", "encrypted", "decrypt"
#         ]
#     },
#     "database": {
#         "main": "database",
#         "subcategories": [
#             "database", "db", "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite",
#             "d@tab@s3", "d@t@b@se", "d8tabase", "d@t@b4s3", "table", "schema", "query",
#             "backup", "dump", "export", "import", "connection", "server", "host", "port"
#         ]
#     },
#     "credentials": {
#         "main": "credentials",
#         "subcategories": [
#             "credentials", "creds", "username", "user", "account", "profile", "identity",
#             "cr3d3ntial$", "cred3ntialz", "cr3ds", "cr3d5", "login", "access", "permission",
#             "role", "privilege", "authorization", "certificate", "key", "keyfile", "private"
#         ]
#     },
#     "email": {
#         "main": "email",
#         "subcategories": [
#             "email", "mail", "e-mail", "address", "inbox", "smtp", "pop3", "imap",
#             "3m@il", "e-m@il", "em4il", "em@i1", "message", "sender", "recipient",
#             "domain", "mailbox", "contact", "newsletter", "subscription", "unsubscribe"
#         ]
#     },
#     "leak": {
#         "main": "leak",
#         "subcategories": [
#             "leak", "breach", "exposed", "dump", "stolen", "hacked", "compromised",
#             "l3ak", "l34k", "l3@k", "l3@kz", "data", "information", "confidential",
#             "sensitive", "private", "personal", "exploit", "vulnerability", "security"
#         ]
#     },
#     "search_term": {
#         "main": "search_term",
#         "subcategories": []  # Will be populated dynamically with the actual search term
#     }
# }

# # Configuration
# current_path = pathlib.Path(__file__).parent.resolve()
# user_agents_json = read_json(f"{current_path}/utils/desktop_agents.json")

# PROXY = {
#     'http': 'socks5h://localhost:9050',
#     'https': 'socks5h://localhost:9050'
# }

# user_agents = user_agents_json.get("agents", [])

# def get_all_keywords():
#     """Get all keywords from all categories"""
#     all_keywords = []
#     for category_data in KEYWORD_CATEGORIES.values():
#         all_keywords.extend(category_data["subcategories"])
#     return list(set(all_keywords))  # Remove duplicates

# def categorize_found_keywords(found_keywords, search_term=None):
#     """Categorize found keywords into main categories"""
#     categorized = {}
    
#     # Clean the search term (strip quotes)
#     search_clean = search_term.strip('"').lower() if search_term else None
    
#     for keyword in found_keywords:
#         keyword_lower = keyword.lower()
#         # Check if this keyword is the search term
#         if search_clean and keyword_lower == search_clean:
#             main_cat = "search_term"
#             if main_cat not in categorized:
#                 categorized[main_cat] = {
#                     "main_category": "search_term",
#                     "found_subcategories": []
#                 }
#             if keyword_lower not in [sub.lower() for sub in categorized[main_cat]["found_subcategories"]]:
#                 categorized[main_cat]["found_subcategories"].append(keyword)
#         else:
#             # Check other categories
#             for main_cat, cat_data in KEYWORD_CATEGORIES.items():
#                 if main_cat == "search_term":
#                     continue  # Skip the search_term category for regular keywords
#                 if keyword_lower in [sub.lower() for sub in cat_data["subcategories"]]:
#                     if main_cat not in categorized:
#                         categorized[main_cat] = {
#                             "main_category": cat_data["main"],
#                             "found_subcategories": []
#                         }
#                     if keyword_lower not in [sub.lower() for sub in categorized[main_cat]["found_subcategories"]]:
#                         categorized[main_cat]["found_subcategories"].append(keyword)
    
#     return categorized

# def search_url_categorized(result_entry, search, keyword_list):
#     """
#     Enhanced search function that categorizes found keywords and creates structured results.
    
#     :param result_entry: A dictionary from results containing {"engine": ..., "link": ...}.
#     :param search: The keyword being searched.
#     :param keyword_list: List of keywords to search for.
#     :return: A structured dictionary containing categorized findings.
#     """
#     print(f"🔍 Processing result_entry: {result_entry} (Type: {type(result_entry)})")
    
#     if not isinstance(result_entry, dict):
#         print(f"⚠️ Expected dictionary, but got {type(result_entry)}: {result_entry}")
#         return None
    
#     torurl = result_entry.get("link", "").strip()
#     search_engine = result_entry.get("engine", "unknown")
    
#     if not torurl.startswith("http://"):
#         torurl = f"http://{torurl}"
    
#     # Create session for this process
#     session = requests.Session()
#     session.proxies = {
#         'http': 'socks5h://localhost:9050',
#         'https': 'socks5h://localhost:9050'
#     }
    
#     retries = 1
#     page_text = ""
    
#     for attempt in range(retries):
#         random_user_agent = random.choice(user_agents)
#         headers = {"User-Agent": random_user_agent}
        
#         try:
#             response = session.get(torurl, timeout=10)
#             response.raise_for_status()

#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Remove unwanted elements
#             for element in soup([
#                 "script", "style", "meta", "noscript", "iframe", "object", "embed",
#                 "head", "header", "footer", "nav", "aside", "form", "button", "svg",
#                 "canvas", "link", "select", "input", "textarea", "br", "hr"
#             ]):
#                 element.decompose()
            
#             page_text = soup.get_text(separator=' ')
#             page_text = re.sub(r'\s+', ' ', page_text).strip()
            
#             print(f"✅ Successfully scraped {torurl}")
#             break
            
#         except requests.exceptions.RequestException as e:
#             print(f"❌ Error scraping {torurl} (Attempt {attempt+1}/{retries}): {e}")
#             continue
#     else:
#         print(f"🚨 Skipping {torurl} after {retries} failed attempts.")
#         return None
    
#     if not page_text:
#         return None
    
#     text_lower = page_text.lower()
#     words = page_text.split()
#     found_keywords = []
#     keyword_contexts = {}
    
#     # Search for keywords and extract contexts
#     for keyword in keyword_list:
#         if keyword.lower() in text_lower:
#             # Add all found keywords including the search term
#             found_keywords.append(keyword)
#             keyword_lower = keyword.lower()
#             count = text_lower.count(keyword_lower)
            
#             # Get all character positions of the keyword
#             positions = []
#             pos = 0
#             while True:
#                 pos = text_lower.find(keyword_lower, pos)
#                 if pos == -1:
#                     break
#                 positions.append(pos)
#                 pos += len(keyword)
            
#             # Extract contexts with 100 characters before and after each occurrence
#             contexts = []
#             for char_pos in positions:
#                 # Extract 100 characters before and after the keyword
#                 start_char = max(0, char_pos - 100)
#                 end_char = min(len(page_text), char_pos + len(keyword) + 100)
                
#                 # Get the context text
#                 context_text = page_text[start_char:end_char]
                
#                 # Find the keyword position within this context
#                 keyword_start_in_context = char_pos - start_char
#                 keyword_end_in_context = keyword_start_in_context + len(keyword)
                
#                 # Create a structured context with before, keyword, and after parts
#                 before_text = context_text[:keyword_start_in_context]
#                 keyword_text = context_text[keyword_start_in_context:keyword_end_in_context]
#                 after_text = context_text[keyword_end_in_context:]
                
#                 context_obj = {
#                     "full_context": context_text,
#                     "before": before_text,
#                     "keyword": keyword_text,
#                     "after": after_text,
#                     "position": char_pos
#                 }
#                 contexts.append(context_obj)
            
#             keyword_contexts[keyword] = {
#                 "count": count,
#                 "contexts": contexts
#             }
    
#     if not found_keywords:
#         return None
    
#     # Categorize the found keywords (pass search term for proper categorization)
#     categorized_keywords = categorize_found_keywords(found_keywords, search)
    
#     # Debug: Check if search term was found
#     search_clean = search.strip('"').lower()
#     if search_clean in text_lower:
#         print(f"✅ Search term '{search_clean}' found in {torurl}")
#     else:
#         print(f"⚠️ Search term '{search_clean}' NOT found in {torurl}")
    
#     # Create structured result
#     result = {
#         "url": torurl,
#         "search_engine": search_engine,
#         "search_term": search,
#         "scan_timestamp": datetime.now().isoformat(),
#         "total_keywords_found": len(found_keywords),
#         "categories_detected": list(categorized_keywords.keys()),
#         "categorized_findings": categorized_keywords,
#         "keyword_details": keyword_contexts,
#         "page_length": len(page_text)
#     }
    
#     return result

# def create_category_coverage_chart(findings):
#     """
#     Create a horizontal bar chart showing category coverage (how many of total categories were found).
#     Shows X out of 5 categories found as a single progress bar.
#     Returns a BytesIO buffer containing the chart image.
#     """
#     # Get all possible categories from KEYWORD_CATEGORIES
#     total_categories = len(KEYWORD_CATEGORIES)
    
#     # Get unique categories detected across all findings
#     detected_categories = set()
#     for finding in findings:
#         categories = finding.get('categories_detected', [])
#         detected_categories.update(categories)
    
#     found_count = len(detected_categories)
#     not_found_count = total_categories - found_count
#     coverage_percentage = (found_count / total_categories) * 100
    
#     if found_count == 0:
#         return None
    
#     # Create horizontal bar chart with compact size
#     fig, ax = plt.subplots(figsize=(8, 1.5))  # Reduced height from 2.5 to 1.5
    
#     # Create stacked horizontal bar
#     categories = ['Category Coverage']
#     found = [found_count]
#     not_found = [not_found_count]
    
#     # Plot the bars
#     bar1 = ax.barh(categories, found, color='#52B788', label=f'Found ({found_count})')
#     bar2 = ax.barh(categories, not_found, left=found, color='#E63946', label=f'Not Found ({not_found_count})')
    
#     # Add percentage text in the middle of found section
#     if found_count > 0:
#         ax.text(found_count / 2, 0, f'{coverage_percentage:.1f}%', 
#                 ha='center', va='center', color='white', fontsize=14, fontweight='bold')
    
#     # Add text showing the fraction
#     ax.text(total_categories + 0.3, 0, f'{found_count}/{total_categories} Categories Detected', 
#             ha='left', va='center', fontsize=12, fontweight='bold')
    
#     # Customize the chart
#     ax.set_xlim(0, total_categories + 2)
#     ax.set_xlabel('Number of Categories', fontsize=11, fontweight='bold')
#     ax.set_title('Category Coverage Analysis', fontsize=13, fontweight='bold', pad=5)  # Minimal padding
#     ax.legend(loc='upper right', fontsize=9)
#     ax.set_yticks([])  # Remove y-axis ticks
    
#     # Add grid for easier reading
#     ax.grid(axis='x', alpha=0.3, linestyle='--')
    
#     # Remove all extra whitespace
#     plt.subplots_adjust(top=0.85, bottom=0.15, left=0.05, right=0.95)
    
#     # Save to buffer with NO padding
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0)  # Zero padding!
#     buf.seek(0)
#     plt.close(fig)
    
#     return buf

# def create_keyword_frequency_chart(findings):
#     """
#     Create a horizontal bar chart showing the most frequently detected keywords.
#     Returns a BytesIO buffer containing the chart image.
#     """
#     # Count all keywords across all findings
#     keyword_counts = Counter()
#     for finding in findings:
#         keyword_details = finding.get('keyword_details', {})
#         for keyword, details in keyword_details.items():
#             keyword_counts[keyword] += details.get('count', 0)
    
#     if not keyword_counts:
#         return None
    
#     # Get top 15 keywords
#     top_keywords = keyword_counts.most_common(15)
    
#     if not top_keywords:
#         return None
    
#     # Create horizontal bar chart
#     fig, ax = plt.subplots(figsize=(8, 6))
#     keywords = [k[0] for k in top_keywords]
#     counts = [k[1] for k in top_keywords]
    
#     # Create gradient colors
#     colors_gradient = plt.cm.RdYlGn_r(range(len(keywords)))
    
#     y_pos = range(len(keywords))
#     bars = ax.barh(y_pos, counts, color=colors_gradient)
    
#     ax.set_yticks(y_pos)
#     ax.set_yticklabels(keywords, fontsize=9)
#     ax.invert_yaxis()  # Labels read top-to-bottom
#     ax.set_xlabel('Frequency', fontsize=11, fontweight='bold')
#     ax.set_title('Top 15 Most Frequently Detected Keywords', fontsize=14, fontweight='bold', pad=5)  # Minimal padding
    
#     # Add value labels on bars
#     for i, (bar, count) in enumerate(zip(bars, counts)):
#         width = bar.get_width()
#         ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
#                 f'{int(count)}', ha='left', va='center', fontsize=9, fontweight='bold')
    
#     # Remove all extra whitespace
#     plt.subplots_adjust(top=0.95, bottom=0.08, left=0.15, right=0.95)
    
#     # Save to buffer with NO padding
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0)  # Zero padding!
#     buf.seek(0)
#     plt.close(fig)
    
#     return buf

# def create_keywords_per_category_pie_chart(findings):
#     """
#     Create a pie chart showing the distribution of globally unique keywords found per category.
#     Returns a BytesIO buffer containing the chart image.
#     """
#     # Count GLOBALLY unique keywords by category (no duplicates across sites)
#     # Use keyword_details (same source as summary) for consistency
#     from collections import defaultdict
#     category_keyword_sets = defaultdict(set)
#     already_assigned = set()  # Track keywords already assigned to a category
    
#     # First, get all unique keywords
#     all_keywords_by_category = defaultdict(set)
#     for finding in findings:
#         keyword_details = finding.get('keyword_details', {})
#         categorized = finding.get('categorized_findings', {})
        
#         # For each keyword found in the page
#         for keyword in keyword_details.keys():
#             # Skip if already assigned to a category (avoid double counting)
#             if keyword in already_assigned:
#                 continue
            
#             # Find which category this keyword belongs to (assign to first match only)
#             for category, cat_details in categorized.items():
#                 if keyword in cat_details.get('found_subcategories', []):
#                     category_keyword_sets[category].add(keyword)
#                     already_assigned.add(keyword)
#                     break  # Assign to first category only
    
#     # Convert sets to counts
#     category_keyword_counts = {cat: len(keywords) for cat, keywords in category_keyword_sets.items()}
    
#     if not category_keyword_counts:
#         return None
    
#     # Sort by count for better visualization
#     sorted_categories = sorted(category_keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
#     # Create pie chart
#     fig, ax = plt.subplots(figsize=(7, 7))
#     categories = [c[0] for c in sorted_categories]
#     counts = [c[1] for c in sorted_categories]
    
#     # Color scheme - vibrant and distinct colors
#     colors_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
#                       '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
    
#     # Create labels with both category name and count
#     # Format category names nicely (capitalize, replace underscores)
#     formatted_categories = []
#     for cat in categories:
#         if cat == 'search_term':
#             formatted_cat = 'Search Term'
#         else:
#             formatted_cat = cat.replace('_', ' ').title()
#         formatted_categories.append(formatted_cat)
    
#     labels_with_counts = [f'{cat}\n({count} keywords)' for cat, count in zip(formatted_categories, counts)]
    
#     wedges, texts, autotexts = ax.pie(counts, labels=labels_with_counts, autopct='%1.1f%%',
#                                         startangle=90, colors=colors_palette[:len(categories)])
    
#     # Make percentage text more readable
#     for autotext in autotexts:
#         autotext.set_color('white')
#         autotext.set_fontweight('bold')
#         autotext.set_fontsize(10)
    
#     # Make label text more readable
#     for text in texts:
#         text.set_fontsize(9)
#         text.set_fontweight('bold')
    
#     # Calculate total keywords
#     total_keywords = sum(counts)
#     ax.set_title(f'Keywords Distribution by Category\nTotal: {total_keywords} unique keywords found', 
#                  fontsize=14, fontweight='bold', pad=5)  # Minimal title padding
    
#     # Remove all extra whitespace
#     plt.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.95)
    
#     # Save to buffer with NO padding
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0)  # Zero padding!
#     buf.seek(0)
#     plt.close(fig)
    
#     return buf

# def generate_pdf_report(findings, search_term, summary_stats=None):
#     """
#     Generate a PDF report from the categorized findings.
    
#     :param findings: List of structured findings from search_url_categorized
#     :param search_term: The original search term
#     :param summary_stats: Pre-calculated summary statistics to ensure consistency
#     :return: Base64 encoded PDF content
#     """
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
#     # Styles
#     styles = getSampleStyleSheet()
#     title_style = ParagraphStyle(
#         'CustomTitle',
#         parent=styles['Heading1'],
#         fontSize=18,
#         spaceAfter=30,
#         alignment=TA_CENTER,
#         textColor=colors.darkblue
#     )
    
#     heading_style = ParagraphStyle(
#         'CustomHeading',
#         parent=styles['Heading2'],
#         fontSize=14,
#         spaceAfter=12,
#         textColor=colors.darkred
#     )
    
#     normal_style = styles['Normal']
    
#     # Build the document
#     story = []
    
#     # Title
#     story.append(Paragraph(f"Dark Web Security Scan Report", title_style))
#     story.append(Paragraph(f"Search Term: {search_term}", styles['Heading3']))
#     story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
#     story.append(Spacer(1, 20))
    
#     # Executive Summary - use pre-calculated stats if provided
#     if summary_stats:
#         total_sites = summary_stats['total_sites']
#         total_keywords = summary_stats['total_keywords']
#         total_categories = summary_stats['categories_found']
#         risk_level = summary_stats['risk_level']
#     else:
#         # Fallback calculation if no pre-calculated stats
#         total_sites = len(findings)
#         total_categories = set()
#         total_keywords = 0
        
#         for finding in findings:
#             total_categories.update(finding.get('categories_detected', []))
#             total_keywords += finding.get('total_keywords_found', 0)
        
#         total_categories = list(total_categories)
#         risk_level = 'HIGH' if total_keywords > 10 else 'MEDIUM' if total_keywords > 5 else 'LOW'
    
#     story.append(Paragraph("Executive Summary", heading_style))
#     summary_data = [
#         ['Metric', 'Value'],
#         ['Sites Scanned', str(total_sites)],
#         ['Total Keywords Found', str(total_keywords)],
#         ['Categories Detected', ', '.join(total_categories)],
#         ['Risk Level', risk_level]
#     ]
    
#     summary_table = Table(summary_data)
#     summary_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 12),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black)
#     ]))
    
#     story.append(summary_table)
#     story.append(Spacer(1, 20))
    
#     # Add Visual Analytics Section
#     if findings and total_keywords > 0:
#         story.append(Paragraph("Visual Analytics", heading_style))
#         story.append(Spacer(1, 8))
        
#         # Generate and add category coverage chart (X out of 5 categories found)
#         coverage_chart_buf = create_category_coverage_chart(findings)
#         if coverage_chart_buf:
#             coverage_img = RLImage(coverage_chart_buf, width=6*inch, height=1*inch)
#             story.append(coverage_img)
#             story.append(Spacer(1, 1))  # Minimal spacing - almost touching
        
#         # Generate and add keywords per category pie chart
#         keywords_per_cat_buf = create_keywords_per_category_pie_chart(findings)
#         if keywords_per_cat_buf:
#             keywords_cat_img = RLImage(keywords_per_cat_buf, width=5*inch, height=3*inch)
#             story.append(keywords_cat_img)
#             story.append(Spacer(1, 1))  # Minimal spacing - almost touching
        
#         # Generate and add keyword frequency bar chart
#         keyword_freq_buf = create_keyword_frequency_chart(findings)
#         if keyword_freq_buf:
#             keyword_img = RLImage(keyword_freq_buf, width=5.5*inch, height=4*inch)
#             story.append(keyword_img)
#             story.append(Spacer(1, 15))  # Reduced from 20 to 15
    
#     # Detailed Findings
#     story.append(Paragraph("Detailed Findings", heading_style))
    
#     for i, finding in enumerate(findings, 1):
#         story.append(Paragraph(f"Site {i}: {finding.get('url', 'Unknown URL')}", styles['Heading4']))
        
#         # Categories found
#         categories = finding.get('categorized_findings', {})
#         if categories:
#             story.append(Paragraph("Categories Detected:", styles['Heading5']))
#             for category, details in categories.items():
#                 story.append(Paragraph(f"• {category.upper()}: {', '.join(details['found_subcategories'])}", normal_style))
        
#             # Full context excerpts
#             keyword_details = finding.get('keyword_details', {})
#             if keyword_details:
#                 story.append(Paragraph("Full Context Excerpts:", styles['Heading5']))
#                 for keyword, details in keyword_details.items():
#                     if details['contexts']:
#                         story.append(Paragraph(f"Keyword '{keyword}' (found {details['count']} times):", styles['Heading6']))
#                         for idx, context_obj in enumerate(details['contexts']):  # Show ALL occurrences
#                             if isinstance(context_obj, dict):
#                                 # Clean HTML tags from context text for PDF
#                                 before_clean = re.sub(r'<[^>]+>', '', context_obj['before'])
#                                 keyword_clean = re.sub(r'<[^>]+>', '', context_obj['keyword'])
#                                 after_clean = re.sub(r'<[^>]+>', '', context_obj['after'])
#                                 context_text = f"...{before_clean}**{keyword_clean}**{after_clean}..."
#                             else:
#                                 # Fallback for old format - clean HTML tags
#                                 raw_text = str(context_obj)[:300] + "..." if len(str(context_obj)) > 300 else str(context_obj)
#                                 context_text = re.sub(r'<[^>]+>', '', raw_text)
                            
#                             # Escape any remaining problematic characters for PDF
#                             context_text = context_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
#                             story.append(Paragraph(f"Occurrence {idx + 1}: {context_text}", normal_style))
        
#         story.append(Spacer(1, 15))
    
#     # Build PDF
#     doc.build(story)
    
#     # Get PDF content and encode as base64
#     pdf_content = buffer.getvalue()
#     buffer.close()
    
#     return base64.b64encode(pdf_content).decode('utf-8')

# def run_categorized_search(mp_units, func_args):
#     """
#     Run multiprocessing for categorized keyword search.
    
#     :param mp_units: Number of processing units.
#     :param func_args: List of function arguments for multiprocessing.
#     :return: List of structured findings.
#     """
#     all_findings = []
#     print(f"🛠️ func_args being passed: {len(func_args)} entries")

#     units = mp_units if mp_units and mp_units > 0 else max((cpu_count() - 1), 1)
#     print(f"Categorized search started with {units} processing units...")
#     freeze_support()

#     with Pool(units) as p:
#         try:
#             results_list = p.starmap(search_url_categorized, func_args)
            
#             # Filter out None results and collect findings
#             for res in results_list:
#                 if res is not None:
#                     all_findings.append(res)

#         except Exception as e:
#             print(f"❌ Error in multiprocessing: {e}")

#     return all_findings

# def main_categorized_search(search, mp_units, results, engine_status=None):
#     """
#     Main function to run categorized keyword search and generate report.
    
#     :param search: Search string.
#     :param mp_units: Number of processing units.
#     :param results: List of search results containing extracted links.
#     :param engine_status: Dictionary containing up_engines and down_engines lists.
#     :return: Dictionary containing findings and PDF report.
#     """
#     print("🚀 Starting categorized keyword analysis...")

#     if not results:
#         print("\nNo results exist.")
#         return {
#             "findings": [], 
#             "pdf_report": None, 
#             "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
#             "engine_status": engine_status or {"up_engines": [], "down_engines": []}
#         }

#     print(f"🔎 Processing {len(results)} links...")
    
#     # Get all keywords from categories
#     keyword_list = get_all_keywords()
#     # Add the search term (strip quotes if present for exact matching)
#     search_clean = search.strip('"').lower()
#     keyword_list.append(search_clean)

#     # Prepare function arguments
#     func_args = [(entry, search, keyword_list) for entry in results]

#     if func_args:
#         findings = run_categorized_search(mp_units, func_args)
        
#         if findings:
#             # Create summary first to ensure consistency
#             total_categories = set()
#             # Count GLOBALLY UNIQUE keywords across all sites
#             all_unique_keywords = set()
#             for finding in findings:
#                 total_categories.update(finding.get('categories_detected', []))
#                 # Add all keywords from this finding to global set
#                 keyword_details = finding.get('keyword_details', {})
#                 all_unique_keywords.update(keyword_details.keys())
            
#             total_keywords = len(all_unique_keywords)
            
#             summary = {
#                 "total_sites": len(findings),
#                 "total_keywords": total_keywords,
#                 "categories_found": list(total_categories),
#                 "risk_level": "HIGH" if total_keywords > 10 else "MEDIUM" if total_keywords > 5 else "LOW"
#             }
            
#             # Generate PDF report using the same findings data and pre-calculated summary
#             pdf_report = generate_pdf_report(findings, search, summary)
            
#             return {
#                 "findings": findings,
#                 "pdf_report": pdf_report,
#                 "summary": summary,
#                 "engine_status": engine_status or {"up_engines": [], "down_engines": []}
#             }
#         else:
#             return {
#                 "findings": [], 
#                 "pdf_report": None, 
#                 "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
#                 "engine_status": engine_status or {"up_engines": [], "down_engines": []}
#             }
#     else:
#         print("\n⚠️ No valid URLs to process.")
#         return {
#             "findings": [], 
#             "pdf_report": None, 
#             "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
#             "engine_status": engine_status or {"up_engines": [], "down_engines": []}
#         }




import requests
import pathlib
from utils.file_helpers import read_json
import argparse
import multiprocessing
from multiprocessing import cpu_count, freeze_support
import random
from bs4 import BeautifulSoup
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image as RLImage
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

# Structured keyword categories
KEYWORD_CATEGORIES = {
    "search_term": {
        "main": "search_term",
        "subcategories": []  # Populated dynamically with the actual search term
    },
    "password": {
        "main": "password",
        "subcategories": [
            "password", "passwd", "pwd", "pass", "passphrase", "secret", "pin", "code",
            "p4ssw0rd", "p@ssw0rd", "p@$$word", "p455w0rd", "authentication", "auth",
            "login", "signin", "credential", "token", "hash", "encrypted", "decrypt"
        ]
    },
    "database": {
        "main": "database",
        "subcategories": [
            "database", "db", "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite",
            "d@tab@s3", "d@t@b@se", "d8tabase", "d@t@b4s3", "table", "schema", "query",
            "backup", "dump", "export", "import", "connection", "server", "host", "port"
        ]
    },
    "credentials": {
        "main": "credentials",
        "subcategories": [
            "credentials", "creds", "username", "user", "account", "profile", "identity",
            "cr3d3ntial$", "cred3ntialz", "cr3ds", "cr3d5", "login", "access", "permission",
            "role", "privilege", "authorization", "certificate", "key", "keyfile", "private"
        ]
    },
    "email": {
        "main": "email",
        "subcategories": [
            "email", "mail", "e-mail", "address", "inbox", "smtp", "pop3", "imap",
            "3m@il", "e-m@il", "em4il", "em@i1", "message", "sender", "recipient",
            "domain", "mailbox", "contact", "newsletter", "subscription", "unsubscribe"
        ]
    },
    "leak": {
        "main": "leak",
        "subcategories": [
            "leak", "breach", "exposed", "dump", "stolen", "hacked", "compromised",
            "l3ak", "l34k", "l3@k", "l3@kz", "data", "information", "confidential",
            "sensitive", "private", "personal", "exploit", "vulnerability", "security"
        ]
    }
}

# Configuration
current_path = pathlib.Path(__file__).parent.resolve()
user_agents_json = read_json(f"{current_path}/utils/desktop_agents.json")

PROXY = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}

user_agents = user_agents_json.get("agents", [])

def get_all_keywords():
    """Get all keywords from all categories"""
    all_keywords = []
    for category_data in KEYWORD_CATEGORIES.values():
        all_keywords.extend(category_data["subcategories"])
    return list(set(all_keywords))

def categorize_found_keywords(found_keywords, search_term=None):
    """Categorize found keywords into main categories"""
    categorized = {}
    search_clean = search_term.strip('"').lower() if search_term else None
    
    for keyword in found_keywords:
        keyword_lower = keyword.lower()
        if search_clean and keyword_lower == search_clean:
            main_cat = "search_term"
            if main_cat not in categorized:
                categorized[main_cat] = {
                    "main_category": "search_term",
                    "found_subcategories": []
                }
            if keyword_lower not in [sub.lower() for sub in categorized[main_cat]["found_subcategories"]]:
                categorized[main_cat]["found_subcategories"].append(keyword)
        else:
            for main_cat, cat_data in KEYWORD_CATEGORIES.items():
                if main_cat == "search_term":
                    continue
                if keyword_lower in [sub.lower() for sub in cat_data["subcategories"]]:
                    if main_cat not in categorized:
                        categorized[main_cat] = {
                            "main_category": cat_data["main"],
                            "found_subcategories": []
                        }
                    if keyword_lower not in [sub.lower() for sub in categorized[main_cat]["found_subcategories"]]:
                        categorized[main_cat]["found_subcategories"].append(keyword)
    
    return categorized

def search_url_categorized(result_entry, search, keyword_list):
    """Enhanced search function that categorizes found keywords and creates structured results."""
    print(f"🔍 Processing result_entry: {result_entry} (Type: {type(result_entry)})")
    
    if not isinstance(result_entry, dict):
        print(f"⚠️ Expected dictionary, but got {type(result_entry)}: {result_entry}")
        return None
    
    torurl = result_entry.get("link", "").strip()
    search_engine = result_entry.get("engine", "unknown")
    
    if not torurl.startswith("http://"):
        torurl = f"http://{torurl}"
    
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://localhost:9050',
        'https': 'socks5h://localhost:9050'
    }
    
    retries = 1
    page_text = ""
    
    for attempt in range(retries):
        random_user_agent = random.choice(user_agents)
        headers = {"User-Agent": random_user_agent}
        
        try:
            response = session.get(torurl, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for element in soup([
                "script", "style", "meta", "noscript", "iframe", "object", "embed",
                "head", "header", "footer", "nav", "aside", "form", "button", "svg",
                "canvas", "link", "select", "input", "textarea", "br", "hr"
            ]):
                element.decompose()
            
            page_text = soup.get_text(separator=' ')
            page_text = re.sub(r'\s+', ' ', page_text).strip()
            print(f"✅ Successfully scraped {torurl}")
            break
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error scraping {torurl} (Attempt {attempt+1}/{retries}): {e}")
            continue
    else:
        print(f"🚨 Skipping {torurl} after {retries} failed attempts.")
        return None
    
    if not page_text:
        return None
    
    text_lower = page_text.lower()
    found_keywords = []
    keyword_contexts = {}
    
    # Clean search term for comparison
    search_clean = search.strip('"').lower() if search else None
    
    for keyword in keyword_list:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            
            # Use 300 characters for search term, 100 for other keywords
            is_search_term = (search_clean and keyword_lower == search_clean)
            context_chars = 300 if is_search_term else 100
            
            positions = []
            pos = 0
            while True:
                pos = text_lower.find(keyword_lower, pos)
                if pos == -1:
                    break
                positions.append(pos)
                pos += len(keyword)
            
            contexts = []
            for char_pos in positions:
                start_char = max(0, char_pos - context_chars)
                end_char = min(len(page_text), char_pos + len(keyword) + context_chars)
                context_text = page_text[start_char:end_char]
                keyword_start_in_context = char_pos - start_char
                keyword_end_in_context = keyword_start_in_context + len(keyword)
                
                before_text = context_text[:keyword_start_in_context]
                keyword_text = context_text[keyword_start_in_context:keyword_end_in_context]
                after_text = context_text[keyword_end_in_context:]
                
                context_obj = {
                    "full_context": context_text,
                    "before": before_text,
                    "keyword": keyword_text,
                    "after": after_text,
                    "position": char_pos
                }
                contexts.append(context_obj)
            
            keyword_contexts[keyword] = {
                "count": count,
                "contexts": contexts
            }
    
    if not found_keywords:
        return None
    
    categorized_keywords = categorize_found_keywords(found_keywords, search)
    
    result = {
        "url": torurl,
        "search_engine": search_engine,
        "search_term": search,
        "scan_timestamp": datetime.now().isoformat(),
        "total_keywords_found": len(found_keywords),
        "categories_detected": list(categorized_keywords.keys()),
        "categorized_findings": categorized_keywords,
        "keyword_details": keyword_contexts,
        "page_length": len(page_text)
    }
    
    return result

def create_category_coverage_chart(findings):
    """Create a horizontal bar chart showing category coverage."""
    total_categories = len(KEYWORD_CATEGORIES)
    detected_categories = set()
    for finding in findings:
        categories = finding.get('categories_detected', [])
        detected_categories.update(categories)
    
    found_count = len(detected_categories)
    not_found_count = total_categories - found_count
    coverage_percentage = (found_count / total_categories) * 100
    
    if found_count == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(6, 1.8))
    categories = ['Category Coverage']
    found = [found_count]
    not_found = [not_found_count]
    
    bar1 = ax.barh(categories, found, color='#0D47A1', label=f'Found ({found_count})')  # Darkest blue
    bar2 = ax.barh(categories, not_found, left=found, color='#E3F2FD', label=f'Not Found ({not_found_count})')  # Lightest blue
    
    # Add percentage text inside the found bar
    # if found_count > 0:
    #     ax.text(found_count / 2, 0, f'{coverage_percentage:.1f}%', 
    #             ha='center', va='center', color='white', fontsize=13, fontweight='bold')
    
    # # Add text showing the fraction outside the bar
    # ax.text(total_categories + 0.3, 0, f'{found_count}/{total_categories} Categories', 
    #         ha='left', va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlim(0, total_categories)  # Set limit to exact number of categories
    ax.set_xlabel('Number of Categories', fontsize=10, fontweight='bold')
    ax.set_title('Category Coverage Analysis', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_yticks([])
    ax.set_xticks(range(1, total_categories + 1))  # Show 0, 1, 2, 3, 4, 5, 6
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.05)
    buf.seek(0)
    plt.close(fig)
    
    return buf

def create_keyword_frequency_chart(findings):
    """Create a horizontal bar chart showing the most frequently detected keywords."""
    keyword_counts = Counter()
    for finding in findings:
        keyword_details = finding.get('keyword_details', {})
        for keyword, details in keyword_details.items():
            keyword_counts[keyword] += details.get('count', 0)
    
    if not keyword_counts:
        return None
    
    top_keywords = keyword_counts.most_common(15)
    if not top_keywords:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    keywords = [k[0] for k in top_keywords]
    counts = [k[1] for k in top_keywords]
    
    # Simple blue gradient - darker blue for higher frequency
    # Reverse the order so highest frequency gets darkest blue
    blues_values = list(range(100, 255, 10))[:len(keywords)]
    blues_values.reverse()  # Reverse so first (highest frequency) is darkest
    colors_gradient = plt.cm.Blues([v for v in blues_values])
    y_pos = range(len(keywords))
    bars = ax.barh(y_pos, counts, color=colors_gradient)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(keywords, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Frequency', fontsize=11, fontweight='bold')
    ax.set_title('Top 15 Most Frequently Detected Keywords', fontsize=13, fontweight='bold', pad=12)
    
    for i, (bar, count) in enumerate(zip(bars, counts)):
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
                f'{int(count)}', ha='left', va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.05)
    buf.seek(0)
    plt.close(fig)
    
    return buf

def create_keywords_per_category_pie_chart(findings):
    """Create a pie chart showing the distribution of globally unique keywords found per category."""
    from collections import defaultdict
    category_keyword_sets = defaultdict(set)
    already_assigned = set()
    
    for finding in findings:
        keyword_details = finding.get('keyword_details', {})
        categorized = finding.get('categorized_findings', {})
        
        for keyword in keyword_details.keys():
            if keyword in already_assigned:
                continue
            
            for category, cat_details in categorized.items():
                if keyword in cat_details.get('found_subcategories', []):
                    category_keyword_sets[category].add(keyword)
                    already_assigned.add(keyword)
                    break
    
    category_keyword_counts = {cat: len(keywords) for cat, keywords in category_keyword_sets.items()}
    
    if not category_keyword_counts:
        return None
    
    sorted_categories = sorted(category_keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    categories = [c[0] for c in sorted_categories]
    counts = [c[1] for c in sorted_categories]
    
    # Simple blue color palette - different shades of blue
    colors_palette = ['#0D47A1', '#1565C0', '#1976D2', '#1E88E5', '#2196F3', 
                      '#42A5F5', '#64B5F6', '#90CAF9', '#BBDEFB', '#E3F2FD']
    
    formatted_categories = []
    for cat in categories:
        if cat == 'search_term':
            formatted_cat = 'Search Term'
        else:
            formatted_cat = cat.replace('_', ' ').title()
        formatted_categories.append(formatted_cat)
    
    labels_with_counts = [f'{cat}\n({count} keywords)' for cat, count in zip(formatted_categories, counts)]
    
    wedges, texts, autotexts = ax.pie(counts, labels=labels_with_counts, autopct='%1.1f%%',
                                        startangle=90, colors=colors_palette[:len(categories)])
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    for text in texts:
        text.set_fontsize(9)
        text.set_fontweight('bold')
    
    total_keywords = sum(counts)
    ax.set_title(f'Keywords Distribution by Category\nTotal: {total_keywords} unique keywords', 
                 fontsize=12, fontweight='bold', pad=12)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.05)
    buf.seek(0)
    plt.close(fig)
    
    return buf

def generate_pdf_report(findings, search_term, summary_stats=None):
    """Generate a PDF report from the categorized findings."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkred
    )
    
    normal_style = styles['Normal']
    
    story = []
    
    story.append(Paragraph(f"Dark Web Security Scan Report", title_style))
    story.append(Paragraph(f"Search Term: {search_term}", styles['Heading3']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 20))
    
    if summary_stats:
        total_sites = summary_stats['total_sites']
        total_keywords = summary_stats['total_keywords']
        total_categories = summary_stats['categories_found']
    else:
        total_sites = len(findings)
        total_categories = set()
        total_keywords = 0
        
        for finding in findings:
            total_categories.update(finding.get('categories_detected', []))
            total_keywords += finding.get('total_keywords_found', 0)
        
        total_categories = list(total_categories)
    
    story.append(Paragraph("Executive Summary", heading_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Sites Scanned', str(total_sites)],
        ['Total Keywords Found', str(total_keywords)],
        ['Categories Detected', ', '.join(total_categories)]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 25))
    
    # Professional Visual Analytics Section
    if findings and total_keywords > 0:
        story.append(Paragraph("Visual Analytics", heading_style))
        story.append(Spacer(1, 12))
        
        # Generate charts
        coverage_chart_buf = create_category_coverage_chart(findings)
        keywords_per_cat_buf = create_keywords_per_category_pie_chart(findings)
        keyword_freq_buf = create_keyword_frequency_chart(findings)
        
        # Create top row: Coverage bar (left) + Pie chart (right)
        top_row_images = []
        if coverage_chart_buf:
            coverage_img = RLImage(coverage_chart_buf, width=3.2*inch, height=1.2*inch)
            top_row_images.append(coverage_img)
        
        if keywords_per_cat_buf:
            pie_img = RLImage(keywords_per_cat_buf, width=3*inch, height=3*inch)
            top_row_images.append(pie_img)
        
        # Add top row as a table for horizontal alignment
        if len(top_row_images) == 2:
            top_row_table = Table([top_row_images], colWidths=[3.3*inch, 3.2*inch])
            top_row_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),      # Left cell: no left padding
                ('RIGHTPADDING', (0, 0), (0, 0), 10),    # Left cell: 10pt right padding (space between charts)
                ('LEFTPADDING', (1, 0), (1, 0), 10),     # Right cell: 10pt left padding (space between charts)
                ('RIGHTPADDING', (1, 0), (1, 0), 0),     # Right cell: no right padding
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(top_row_table)
            story.append(Spacer(1, 18))
        elif len(top_row_images) == 1:
            story.append(top_row_images[0])
            story.append(Spacer(1, 18))
        
        # Add bottom chart: Frequency bar chart (full width)
        if keyword_freq_buf:
            keyword_img = RLImage(keyword_freq_buf, width=6.5*inch, height=3.5*inch)
            story.append(keyword_img)
            story.append(Spacer(1, 20))
    
    # Detailed Findings
    story.append(Paragraph("Detailed Findings", heading_style))
    
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"Site {i}: {finding.get('url', 'Unknown URL')}", styles['Heading4']))
        
        categories = finding.get('categorized_findings', {})
        if categories:
            story.append(Paragraph("Categories Detected:", styles['Heading5']))
            for category, details in categories.items():
                story.append(Paragraph(f"• {category.upper()}: {', '.join(details['found_subcategories'])}", normal_style))
        
            keyword_details = finding.get('keyword_details', {})
            if keyword_details:
                story.append(Paragraph("Full Context Excerpts:", styles['Heading5']))
                
                # Sort keywords so search term appears first
                search_clean = search_term.strip('"').lower()
                sorted_keywords = sorted(keyword_details.items(), 
                                       key=lambda x: (x[0].lower() != search_clean, x[0]))
                
                for keyword, details in sorted_keywords:
                    if details['contexts']:
                        story.append(Paragraph(f"Keyword '{keyword}' (found {details['count']} times):", styles['Heading6']))
                        for idx, context_obj in enumerate(details['contexts']):
                            if isinstance(context_obj, dict):
                                before_clean = re.sub(r'<[^>]+>', '', context_obj['before'])
                                keyword_clean = re.sub(r'<[^>]+>', '', context_obj['keyword'])
                                after_clean = re.sub(r'<[^>]+>', '', context_obj['after'])
                                
                                # Escape special characters
                                before_clean = before_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                keyword_clean = keyword_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                after_clean = after_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                
                                # Highlight keyword with yellow background
                                context_text = f"...{before_clean}<b><font backColor='yellow'>{keyword_clean}</font></b>{after_clean}..."
                            else:
                                raw_text = str(context_obj)[:300] + "..." if len(str(context_obj)) > 300 else str(context_obj)
                                context_text = re.sub(r'<[^>]+>', '', raw_text)
                                context_text = context_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            
                            story.append(Paragraph(f"Occurrence {idx + 1}: {context_text}", normal_style))
        
        story.append(Spacer(1, 15))
    
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_content).decode('utf-8')

def run_categorized_search(mp_units, func_args):
    """Run multiprocessing for categorized keyword search."""
    all_findings = []
    print(f"🛠️ func_args being passed: {len(func_args)} entries")

    units = mp_units if mp_units and mp_units > 0 else max((cpu_count() - 1), 1)
    print(f"Categorized search started with {units} processing units...")

    # Use 'spawn' context to avoid fork-in-thread deadlocks when
    # multiple scans run in parallel from worker threads.
    ctx = multiprocessing.get_context("spawn")
    freeze_support()

    with ctx.Pool(units) as p:
        try:
            results_list = p.starmap(search_url_categorized, func_args)
            for res in results_list:
                if res is not None:
                    all_findings.append(res)
        except Exception as e:
            print(f"❌ Error in multiprocessing: {e}")

    return all_findings

def main_categorized_search(search, mp_units, results, engine_status=None):
    """Main function to run categorized keyword search and generate report."""
    print("🚀 Starting categorized keyword analysis...")

    if not results:
        print("\nNo results exist.")
        return {
            "findings": [], 
            "pdf_report": None, 
            "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
            "engine_status": engine_status or {"up_engines": [], "down_engines": []}
        }

    print(f"🔎 Processing {len(results)} links...")
    
    keyword_list = get_all_keywords()
    search_clean = search.strip('"').lower()
    keyword_list.append(search_clean)

    func_args = [(entry, search, keyword_list) for entry in results]

    if func_args:
        findings = run_categorized_search(mp_units, func_args)
        
        if findings:
            total_categories = set()
            all_unique_keywords = set()
            for finding in findings:
                total_categories.update(finding.get('categories_detected', []))
                keyword_details = finding.get('keyword_details', {})
                all_unique_keywords.update(keyword_details.keys())
            
            total_keywords = len(all_unique_keywords)
            
            summary = {
                "total_sites": len(findings),
                "total_keywords": total_keywords,
                "categories_found": list(total_categories)
            }
            
            pdf_report = generate_pdf_report(findings, search, summary)
            
            return {
                "findings": findings,
                "pdf_report": pdf_report,
                "summary": summary,
                "engine_status": engine_status or {"up_engines": [], "down_engines": []}
            }
        else:
            return {
                "findings": [], 
                "pdf_report": None, 
                "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
                "engine_status": engine_status or {"up_engines": [], "down_engines": []}
            }
    else:
        print("\n⚠️ No valid URLs to process.")
        return {
            "findings": [], 
            "pdf_report": None, 
            "summary": {"total_sites": 0, "total_keywords": 0, "categories_found": []},
            "engine_status": engine_status or {"up_engines": [], "down_engines": []}
        }