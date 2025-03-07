# prompt_templates.py

BLOG_IDEA_PROMPT = """
You are a property inspection expert specializing in generating detailed and professional inspection reports.

I need a comprehensive inspection report for a {niche} property.  
The report should include {num_ideas} key inspection areas and be written in a {tone} tone.  
{include_outline}

For each section of the report:
1. Provide a clear and structured heading
2. Write a concise yet informative description of the inspection criteria (2-3 sentences)
3. If detailed observations are requested, include specific points on potential issues, their severity, and recommended actions

Ensure that the report:
- Covers critical inspection aspects such as structural integrity, safety, utilities, and compliance
- Is professionally structured and suitable for official use
- Maintains clarity and is easy to understand
- Uses industry-standard terminology

Format the report properly with headings, bullet points, and spacing for readability.  
RESPOND ONLY WITH THE INSPECTION REPORT AND NO OTHER TEXT.
"""