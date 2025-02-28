from flask import Flask, render_template_string, request, jsonify, send_file
import pandas as pd
import requests
import boto3
import time
import csv
import os

app = Flask(__name__)

# Mistral API Key (Set this as an env variable)
MISTRAL_API_KEY = "EvkXysjBdiAyDSjCjzvIpIhdQNOZ1jDZ"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# AWS Credentials (Replace with IAM role-based access if possible)
AWS_ACCESS_KEY = "AKIA2FXAD22R3MH4XPFT"
AWS_SECRET_KEY = "1ViZf+fKSMzS1VyUp10T5FXTalTQ7LlQDriAlJ/P"
AWS_REGION = "us-east-1"  # Change to your AWS region
S3_BUCKET = "my-video-analysis-bucket11"

rekognition = boto3.client('rekognition',
                           aws_access_key_id=AWS_ACCESS_KEY,
                           aws_secret_access_key=AWS_SECRET_KEY,
                           region_name=AWS_REGION)

CSV_FILE_PATH = "static/results.csv"

# Modern HTML Template with Navigation Bar and Homepage
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vizora - Video Analysis</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
        }
        .navbar {
            background: #007BFF;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .navbar a {
            color: white;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 600;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .hero {
            background: linear-gradient(135deg, #007BFF, #00BFFF);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
        }
        .hero h1 {
            font-size: 3rem;
            margin: 0;
        }
        .hero p {
            font-size: 1.2rem;
            margin: 1rem 0 0;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        .features {
            display: flex;
            justify-content: space-around;
            margin: 4rem 0;
        }
        .feature {
            text-align: center;
            padding: 1rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            width: 30%;
        }
        .feature h2 {
            font-size: 1.5rem;
            margin: 0;
        }
        .feature p {
            font-size: 1rem;
            color: #666;
        }
        .analysis-section {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .analysis-section input[type="text"] {
            width: 80%;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            font-size: 16px;
        }
        .analysis-section button {
            padding: 10px 20px;
            font-size: 16px;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .analysis-section button:hover {
            background-color: #0056b3;
        }
        .status {
            font-weight: bold;
            margin: 15px 0;
        }
        .download, .llm-summary {
            display: none;
            margin-top: 20px;
        }
        .download a, .llm-summary button {
            padding: 10px 15px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .download a:hover, .llm-summary button:hover {
            background: #218838;
        }
        .llm-summary p {
            text-align: left;
            max-width: 600px;
            margin: auto;
            background: #ffffcc;
            padding: 15px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Home</a>
        <a href="#about">About Us</a>
        <a href="#contact">Contact</a>
    </div>
    <div class="hero">
        <h1>Vizora</h1>
        <p>Solving problems with the power of Computer Vision and Machine Learning.</p>
        <p>We are building powerful eyes that analyze video footage and understand the world better.</p>
    </div>
    <div class="container">
        <div class="features">
            <div class="feature">
                <h2>Video Analysis</h2>
                <p>Analyze video footage to detect objects, scenes, and activities with high accuracy.</p>
            </div>
            <div class="feature">
                <h2>AI Insights</h2>
                <p>Get detailed summaries and insights generated by advanced AI models.</p>
            </div>
            <div class="feature">
                <h2>Fast & Reliable</h2>
                <p>Optimized for speed and reliability, delivering results in seconds.</p>
            </div>
        </div>
        <div class="analysis-section">
            <h2>Analyze Your Video</h2>
            <input type="text" id="videoUrl" placeholder="Paste S3 Video URL here" size="60">
            <button onclick="analyzeVideo()">Analyze</button>
            <p class="status" id="statusLabel"></p>
            <div id="downloadSection" class="download">
                <a href="/download">Download CSV Report</a>
            </div>
            <div id="llmSummarySection" class="llm-summary">
                <button onclick="getLLMSummary()">Get AI Summary</button>
                <p id="summaryText"></p>
            </div>
        </div>
    </div>
    <script>
        function analyzeVideo() {
            let videoUrl = document.getElementById("videoUrl").value;
            document.getElementById("statusLabel").innerText = "Processing...";
            document.getElementById("downloadSection").style.display = "none";
            document.getElementById("llmSummarySection").style.display = "none";

            fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_url: videoUrl })
            })
            .then(response => response.json())
            .then(data => {
                let jobId = data.JobId;
                document.getElementById("statusLabel").innerText = "Analysis Started. Job ID: " + jobId;
                setTimeout(() => checkResults(jobId), 5000);  // Reduced polling time
            });
        }

        function checkResults(jobId) {
            fetch(`/get_results?job_id=${jobId}`)
            .then(response => response.json())
            .then(() => {
                document.getElementById("statusLabel").innerText = "Analysis Complete!";
                document.getElementById("downloadSection").style.display = "block";
                document.getElementById("llmSummarySection").style.display = "block";
            });
        }

        function getLLMSummary() {
            document.getElementById("summaryText").innerText = "Generating Summary...";
            fetch("/get_llm_summary")
            .then(response => response.json())
            .then(data => {
                document.getElementById("summaryText").innerText = data.summary;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    video_url = data.get('video_url')

    s3_object_key = video_url.split("/")[-1]

    response = rekognition.start_label_detection(
        Video={'S3Object': {'Bucket': S3_BUCKET, 'Name': s3_object_key}}
    )

    return jsonify({"message": "Analysis started", "JobId": response["JobId"]})

@app.route('/get_results', methods=['GET'])
def get_results():
    job_id = request.args.get('job_id')

    while True:
        response = rekognition.get_label_detection(JobId=job_id)
        if response['JobStatus'] == 'SUCCEEDED':
            break
        time.sleep(3)  # Reduced polling interval

    labels = [{"Timestamp": label["Timestamp"], 
               "Label": label["Label"]["Name"], 
               "Confidence": label["Label"]["Confidence"]} 
              for label in response['Labels']]

    # Save to CSV
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp (ms)", "Label", "Confidence (%)"])
        for label in labels:
            writer.writerow([label["Timestamp"], label["Label"], round(label["Confidence"], 2)])

    return jsonify({"message": "CSV saved!"})

@app.route('/download')
def download():
    return send_file(CSV_FILE_PATH, as_attachment=True)

@app.route('/get_llm_summary')
def get_llm_summary():
    with open(CSV_FILE_PATH, "r") as file:
        csv_data = file.read()

    prompt = f"""
    Here is a CSV file containing detected objects in a video analysis.
    Each row has a timestamp, an object label, and a confidence score.
    Provide a detailed summary of what is happening in the video based on this data.

    CSV Data:
    {csv_data}
    """

    response = requests.post(
        MISTRAL_API_URL,
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "mistral-medium",
            "messages": [
                {"role": "system", "content": "You are an expert in video analysis."},
                {"role": "user", "content": prompt}
            ]
        }
    )

    if response.status_code == 200:
        summary = response.json()["choices"][0]["message"]["content"]
    else:
        summary = f"Error: {response.text}"

    return jsonify({"summary": summary})

if __name__ == '__main__':
    app.run(debug=True)