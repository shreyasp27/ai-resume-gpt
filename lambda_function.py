import json
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib.styles import ParagraphStyle
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
import boto3
import os

s3_client = boto3.client('s3')

# Set up the model
generation_config = {
    "temperature": 0.2,
    "top_p": 1,
    "top_k": 1,
 }

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Initialize your genai model
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# Configure API key
google_api_key = os.environ.get('google_api_key')
genai.configure(api_key = google_api_key)

def update_resume(resume, job_description, about_me):
    prompt = f"Context:\n\nResume:\n{resume}\n\nJob Description:\n{job_description}\n\nAbout Me:\n{about_me}\n\n Update the resume based on the job description to make it more relevant and appealing for the role. Do not add anything else."
    response = model.generate_content(prompt)
    result = response.text.strip()
    return result


def write_cover_letter(resume, job_description, about_me):
    prompt = f"Context:\n\nResume:\n{resume}\n\nJob Description:\n{job_description}\n\nAbout Me:\n{about_me}\n\n Write a compelling cover letter for the job based on the provided information."
    response = model.generate_content(prompt)
    result = response.text.strip()
    return result

def write_personalized_email(resume, job_description, about_me):
    prompt = f"Context:\n\nResume:\n{resume}\n\n\nJob Description:\n{job_description}\n\n\nAbout Me:\n{about_me}\n\n\n Write a personalized email to the hiring manager introducing yourself and expressing your interest in the 'job description' provided. Refer my 'Resume' and 'about me' attached to write the email."
    response = model.generate_content(prompt)
    result = response.text.strip()
    return result

def generate_pdf_buffer(text):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    
    # Define a style for bold text
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        spaceAfter=6,
    )
    
    elements = []
    # Process each paragraph in the text
    paragraphs = text.split("\n")
    for para in paragraphs:
        elements.append(Paragraph(para, bold_style if '**' in para else styles["BodyText"]))
    # Build the PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def generate_docx_buffer(text):
    buffer = BytesIO()
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    for para in text.split("\n"):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(para.replace('**', ''))
        run.bold = '**' in para
    
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def upload_to_s3(buffer, bucket_name, s3_filename):
    buffer.seek(0)
    s3_client.upload_fileobj(buffer, bucket_name, s3_filename)
    
    # Generate pre-signed URL for secure access
    url = s3_client.generate_presigned_url('get_object',
                                           Params={'Bucket': bucket_name, 'Key': s3_filename},
                                           ExpiresIn=3600)
    return url

def lambda_handler(event: APIGatewayProxyEvent, context):
    # Parse the event
    body_str = event.get('body', '{}')
    body = json.loads(body_str) 
    resume = body.get('resume', '')
    job_description = body.get('job_description', '')
    about_me = body.get('about_me', '')
   
    #updated_resume_text = update_resume(resume, job_description, about_me)
    #cover_letter_text = write_cover_letter(resume, job_description, about_me)
    personalized_email = write_personalized_email(resume, job_description, about_me)  
    
    #pdf_buffer = generate_pdf_buffer(updated_resume_text)
    #docx_buffer = generate_docx_buffer(cover_letter_text)
    
    # Note: Adjust the bucket name to your S3 bucket name
    bucket_name = 'ai-resume-gpt'
    resume_key = f'resume.pdf'
    cover_letter_key = f'cover_letter.docx'
    
    # Upload the PDF resume
    #resume_url = upload_to_s3(pdf_buffer, bucket_name, resume_key)
    # Upload the DOCX cover letter
    #cover_letter_url = upload_to_s3(docx_buffer, bucket_name, cover_letter_key)
    
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            #"resume_url": resume_url,
            #"cover_letter_url": cover_letter_url,
            "personalized_email": personalized_email
        })
    }

    return response


