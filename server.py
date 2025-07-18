from flask import Flask, request, jsonify, render_template_string, send_from_directory
import json
import os
from flask_cors import CORS
from datetime import datetime
import requests
import subprocess
import tempfile
import shutil
from video_processor import extract_frames

app = Flask(__name__)
CORS(app)

DATA_FILE = 'synced_data.json'
VIDEO_FILE = 'uploaded_walkthrough.mp4'
OPENAI_API_KEY = 'REMOVED'

@app.route('/sync', methods=['POST'])
def sync():
    data = request.get_json()
    # Add sync time (UTC ISO format)
    data['last_synced'] = datetime.utcnow().isoformat() + 'Z'
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success'})

@app.route('/dashboard')
def dashboard():
    if not os.path.exists(DATA_FILE):
        return '<h2>No data has been synced yet.</h2>'
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    last_synced = data.get('last_synced', None)
    # Modern, Redstone-themed HTML rendering
    html = '''
    <html>
    <head>
    <title>Redstone Maintenance Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', 'Open Sans', Arial, sans-serif;
            background: #f7f7f7;
            color: #222;
            margin: 0;
            padding: 0;
        }
        .header {
            background: #b40000;
            color: #fff;
            padding: 32px 0 10px 0;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        .header h1 {
            margin: 0;
            font-size: 2.3rem;
            font-weight: 700;
            letter-spacing: 1px;
        }
        .last-synced {
            color: #fff;
            font-size: 1.08rem;
            margin-top: 8px;
            opacity: 0.92;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 32px;
            margin: 32px 0 24px 0;
        }
        .stat-card {
            background: #fff;
            color: #b40000;
            padding: 24px 36px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            min-width: 120px;
        }
        .stat-number {
            font-size: 2.1rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 1rem;
            opacity: 0.92;
        }
        .section-title {
            color: #b40000;
            font-size: 1.5rem;
            margin: 32px 0 18px 0;
            font-weight: 700;
        }
        .card-list {
            display: flex;
            flex-wrap: wrap;
            gap: 18px;
            justify-content: flex-start;
        }
        .task-card, .photo-card {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            border: 2px solid #b40000;
            padding: 20px 18px 16px 18px;
            min-width: 260px;
            max-width: 340px;
            flex: 1 1 260px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 12px;
            overflow: hidden;
        }
        .task-title {
            color: #b40000;
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 6px;
            display: flex;
            align-items: flex-end;
            word-break: break-word;
            overflow-wrap: anywhere;
        }
        .task-period {
            background: #b40000;
            color: #fff;
            border-radius: 6px;
            padding: 2px 10px;
            font-size: 0.95rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
        }
        .task-status {
            font-size: 0.98rem;
            font-weight: 600;
            color: #388e3c;
            margin-bottom: 8px;
        }
        .task-status.incomplete {
            color: #d32f2f;
        }
        .photo-img {
            width: 100%;
            max-width: 260px;
            max-height: 140px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 8px;
            box-shadow: 0 2px 8px rgba(229,57,53,0.10);
        }
        .photo-label {
            color: #b40000;
            font-size: 0.98rem;
            font-weight: 600;
        }
        .photo-meta {
            font-size: 0.88rem;
            color: #888;
        }
        .task-footer {
            margin-top: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .nav-links {
            margin-top: 10px;
            text-align: center;
        }
        .nav-link-btn {
            display: inline-block;
            background: #fff;
            color: #b40000;
            border: 2px solid #b40000;
            border-radius: 8px;
            padding: 8px 22px;
            font-size: 1rem;
            font-weight: 600;
            margin: 0 8px;
            text-decoration: none;
            transition: background 0.2s, color 0.2s;
        }
        .nav-link-btn:hover, .nav-link-btn:focus {
            background: #b40000;
            color: #fff;
        }
        @media (max-width: 900px) {
            .stats { flex-direction: column; gap: 12px; }
            .card-list { flex-direction: column; }
        }
    </style>
    </head>
    <body>
        <div class="header">
            <h1>Redstone Maintenance Dashboard</h1>
            <div class="nav-links">
                <a href="/dashboard" class="nav-link-btn">Dashboard</a>
                <a href="/videos" class="nav-link-btn">Videos</a>
            </div>
            {% if last_synced %}<div class="last-synced">Last synced: {{ last_synced.replace('T', ' ')[:-5] }}</div>{% endif %}
        </div>
        {% if video_url or ai_tasks %}
        <div style="max-width:800px;margin:32px auto 0 auto;padding:24px 18px 18px 18px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.07);">
            <div class="section-title" style="margin-top:0;color:#b40000;">Video Walkthrough & AI Tasks</div>
            {% if video_url %}
            <div style="margin-bottom:18px;">
                <video src="{{ video_url }}" controls style="width:100%;max-width:500px;border-radius:8px;"></video>
            </div>
            {% endif %}
            {% if ai_tasks %}
            <div style="margin-bottom:8px;"><strong>AI-Generated Tasks:</strong></div>
            <ul style="padding-left:18px;">
                {% for task in ai_tasks %}
                    <li>{{ task }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ tasks|length }}</div>
                <div class="stat-label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ tasks|selectattr('completed')|list|length }}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ tasks|selectattr('completed', 'equalto', False)|list|length }}</div>
                <div class="stat-label">Remaining</div>
            </div>
        </div>
        <div>
            <div class="section-title">Tasks</div>
            <div class="card-list">
            {% for task in tasks %}
                <div class="task-card">
                    <div class="task-title">{{task['title']}}</div>
                    {% if task.get('filled', {}).get('Extra Details', '').strip() %}
                    <div style="margin: 10px 0 0 0; padding: 8px; background: #fbeaec; border-radius: 8px; color: #b71c1c; font-size: 0.98rem;">
                        <strong>Extra Details:</strong><br>{{ task['filled']['Extra Details'] }}
                    </div>
                    {% endif %}
                    <div class="task-footer">
                        <div class="task-period">{{task['period']|capitalize}}</div>
                        <div class="task-status {% if not task['completed'] %}incomplete{% endif %}">
                            {% if task['completed'] %}Completed{% else %}Incomplete{% endif %}
                        </div>
                    </div>
                </div>
            {% endfor %}
            </div>
        </div>
        <div>
            <div class="section-title">Photos</div>
            <div class="card-list">
            {% for photo in photos %}
                <div class="photo-card">
                    <img src="{{photo['data']}}" class="photo-img"/>
                    <div class="photo-label">{{photo['taskTitle']}}</div>
                    <div class="photo-meta">{{photo['label']}}</div>
                    <div class="photo-meta">{{photo.get('createdAt','')}}</div>
                </div>
            {% endfor %}
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, tasks=data.get('tasks', []), photos=data.get('photos', []), last_synced=last_synced
        , video_url=data.get('video_url'), ai_tasks=data.get('ai_tasks')
    )

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    video = request.files['video']
    # Determine extension
    filename = video.filename or ''
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.webm':
        input_path = 'uploaded_walkthrough.webm'
        output_path = 'uploaded_walkthrough.mp4'
        video.save(input_path)
        print(f"[DEBUG] Converting .webm to .mp4: {input_path} -> {output_path}")
        try:
            ffmpeg_path = r'C:\Users\evanm\Downloads\ffmpeg-2025-07-07-git-d2828ab284-full_build\ffmpeg-2025-07-07-git-d2828ab284-full_build\bin\ffmpeg.exe'
            result = subprocess.run([ffmpeg_path, '-y', '-i', input_path, output_path], capture_output=True, text=True)
            print(f"[DEBUG] ffmpeg stdout: {result.stdout}")
            print(f"[DEBUG] ffmpeg stderr: {result.stderr}")
            if result.returncode != 0:
                return jsonify({'error': 'Failed to convert .webm to .mp4. ffmpeg error.'}), 500
            video_path_for_analysis = output_path
            video_url = '/video/' + output_path
        except Exception as e:
            print(f"[DEBUG] Exception during ffmpeg conversion: {e}")
            return jsonify({'error': f'Exception during ffmpeg conversion: {e}'}), 500
    elif ext == '.mp4':
        input_path = 'uploaded_walkthrough.mp4'
        video.save(input_path)
        video_path_for_analysis = input_path
        video_url = '/video/' + input_path
    else:
        # Save with original extension and try to process as is
        input_path = 'uploaded_walkthrough' + ext
        video.save(input_path)
        video_path_for_analysis = input_path
        video_url = '/video/' + input_path
    # Extract frames using video_processor.py logic
    temp_dir = tempfile.mkdtemp(prefix='frames_')
    try:
        extract_frames(video_path_for_analysis, temp_dir, fps_interval=0.2)
        frame_paths = [os.path.join(temp_dir, f) for f in sorted(os.listdir(temp_dir)) if f.lower().endswith('.jpg')]
        # Limit to first 50 frames for safety
        frame_paths = frame_paths[:50]
        print(f"[DEBUG] Number of frames sent to assistant: {len(frame_paths)}")
        # Call OpenAI API to analyze video and generate tasks in batches
        ai_tasks = analyze_frames_with_openai_assistant(frame_paths)
    finally:
        shutil.rmtree(temp_dir)
    # Store video and tasks in synced_data.json
    data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    data['video_url'] = video_url
    data['ai_tasks'] = ai_tasks
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'video_url': data['video_url'], 'ai_tasks': ai_tasks})

@app.route('/videos')
def videos():
    if not os.path.exists(DATA_FILE):
        return '<h2>No video has been uploaded yet.</h2>'
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    video_url = data.get('video_url')
    ai_tasks = data.get('ai_tasks')
    html = '''
    <html>
    <head>
    <title>Redstone Maintenance Videos</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', 'Open Sans', Arial, sans-serif;
            background: #f7f7f7;
            color: #222;
            margin: 0;
            padding: 0;
        }
        .header {
            background: #b40000;
            color: #fff;
            padding: 32px 0 10px 0;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        .header h1 {
            margin: 0;
            font-size: 2.3rem;
            font-weight: 700;
            letter-spacing: 1px;
        }
        .section-title {
            color: #b40000;
            font-size: 1.5rem;
            margin: 32px 0 18px 0;
            font-weight: 700;
        }
        .video-card {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            padding: 24px 18px 18px 18px;
            max-width: 600px;
            margin: 32px auto;
        }
        video {
            width: 100%;
            max-width: 500px;
            border-radius: 8px;
            margin-bottom: 18px;
        }
        ul {
            padding-left: 18px;
        }
        .nav-links {
            margin-top: 10px;
            text-align: center;
        }
        .nav-link-btn {
            display: inline-block;
            background: #fff;
            color: #b40000;
            border: 2px solid #b40000;
            border-radius: 8px;
            padding: 8px 22px;
            font-size: 1rem;
            font-weight: 600;
            margin: 0 8px;
            text-decoration: none;
            transition: background 0.2s, color 0.2s;
        }
        .nav-link-btn:hover, .nav-link-btn:focus {
            background: #b40000;
            color: #fff;
        }
    </style>
    </head>
    <body>
        <div class="header">
            <h1>Redstone Maintenance Videos</h1>
            <div class="nav-links">
                <a href="/dashboard" class="nav-link-btn">Dashboard</a>
                <a href="/videos" class="nav-link-btn">Videos</a>
            </div>
        </div>
        <div class="video-card">
            <div class="section-title" style="margin-top:0;color:#b40000;">Latest Video Walkthrough & AI Tasks</div>
            {% if video_url %}
            <video src="{{ video_url }}" controls></video>
            {% else %}
            <div style="color:#888;">No video uploaded yet.</div>
            {% endif %}
            {% if ai_tasks %}
            <div style="margin-bottom:8px;"><strong>AI-Generated Tasks:</strong></div>
            <ul>
                {% for task in ai_tasks %}
                    <li>{{ task }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, video_url=video_url, ai_tasks=ai_tasks)

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory('.', filename)

def analyze_frames_with_openai_assistant(frame_paths):
    """
    Analyzes a list of frame paths using the OpenAI Assistant API.
    This function now uploads all frames, sends a single message with all images, and instructs the assistant to respond with tasks for each image.
    """
    import logging
    try:
        import requests
        import time
        import re
    except ImportError:
        return ["Required packages are not installed."]

    assistant_id = "asst_KQlVpUAqWBMzlA246khh67io"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2"
    }
    # 1. Create a new thread
    thread_resp = requests.post("https://api.openai.com/v1/threads", headers=headers)
    if not thread_resp.ok:
        return [f"OpenAI API error (thread creation): {thread_resp.text}"]
    thread_id = thread_resp.json()["id"]

    # 2. Upload all frames and collect file_ids
    file_ids = []
    for idx, frame_path in enumerate(frame_paths):
        with open(frame_path, 'rb') as img_file:
            files = {'file': (f'frame_{idx+1}.jpg', img_file, 'image/jpeg')}
            upload_resp = requests.post(
                "https://api.openai.com/v1/files",
                headers={k: v for k, v in headers.items() if k != "Content-Type"},
                files=files,
                data={'purpose': 'assistants'}
            )
        if not upload_resp.ok:
            return [f"OpenAI API error (file upload): {upload_resp.text}"]
        file_id = upload_resp.json()['id']
        file_ids.append(file_id)

    # 3. Send frames in batches of up to 9 images per message (plus 1 instruction text)
    batch_size = 9
    for i in range(0, len(file_ids), batch_size):
        batch_file_ids = file_ids[i:i+batch_size]
        msg_content = [
            {
                "type": "text",
                "text": (
                    "For each image in this message, analyze it and extract every possible maintenance or cleaning task you can find. "
                    "Respond with bullet points for each image, in order, without mentioning frame numbers or introducing the list. Do not skip any image. Only respond with the tasks themselves. "
                    "At the end, combine all tasks from all images in this message into a single list."
                )
            }
        ]
        for file_id in batch_file_ids:
            msg_content.append({
                "type": "image_file",
                "image_file": {"file_id": file_id}
            })
        msg_data = {
            "role": "user",
            "content": msg_content
        }
        while True:
            msg_resp = requests.post(f"https://api.openai.com/v1/threads/{thread_id}/messages", headers=headers, json=msg_data)
            if msg_resp.ok:
                break
            else:
                try:
                    err = msg_resp.json().get('error')
                    if err and err.get('code') == 'rate_limit_exceeded':
                        wait_match = re.search(r'try again in ([0-9.]+)s', err.get('message', ''))
                        wait_time = float(wait_match.group(1)) if wait_match else 2.0
                        print(f"[DEBUG] Rate limit hit (message), waiting {wait_time} seconds...")
                        time.sleep(wait_time + 0.2)
                        continue
                except Exception:
                    pass
                return [f"OpenAI API error (message add): {msg_resp.text}"]

    # 4. Add a final summary message to compile all tasks
    summary_msg = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Now, please compile all the tasks you found from all previous images in this thread into a single, comprehensive bullet-pointed list. "
                    "Do not skip any image or batch. Only respond with the tasks themselves."
                )
            }
        ]
    }
    while True:
        msg_resp = requests.post(f"https://api.openai.com/v1/threads/{thread_id}/messages", headers=headers, json=summary_msg)
        if msg_resp.ok:
            break
        else:
            try:
                err = msg_resp.json().get('error')
                if err and err.get('code') == 'rate_limit_exceeded':
                    wait_match = re.search(r'try again in ([0-9.]+)s', err.get('message', ''))
                    wait_time = float(wait_match.group(1)) if wait_match else 2.0
                    print(f"[DEBUG] Rate limit hit (summary message), waiting {wait_time} seconds...")
                    time.sleep(wait_time + 0.2)
                    continue
            except Exception:
                pass
            return [f"OpenAI API error (summary message add): {msg_resp.text}"]

    # 5. Run the assistant on the thread
    run_data = {
        "assistant_id": assistant_id
    }
    run_resp = requests.post(f"https://api.openai.com/v1/threads/{thread_id}/runs", headers=headers, json=run_data)
    print(f"[DEBUG] Assistant run response: {run_resp.status_code} {run_resp.text}")
    if not run_resp.ok:
        return [f"OpenAI API error (run start): {run_resp.text}"]
    run_id = run_resp.json()["id"]

    # 6. Poll for run completion
    while True:
        status_resp = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headers)
        if not status_resp.ok:
            return [f"OpenAI API error (run status): {status_resp.text}"]
        status = status_resp.json()["status"]
        if status in ("completed", "failed", "cancelled", "expired"):
            break
        time.sleep(1.5)

    if status != "completed":
        return [f"OpenAI Assistant run did not complete successfully: {status}"]

    # 7. Retrieve the assistant's response
    messages_resp = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/messages", headers=headers)
    if not messages_resp.ok:
        return [f"OpenAI API error (get messages): {messages_resp.text}"]
    messages = messages_resp.json().get("data", [])
    def extract_text(part):
        t = part.get("text")
        if isinstance(t, str):
            return t
        elif isinstance(t, dict):
            return t.get("value") or t.get("content") or str(t)
        return str(t)

    for msg in reversed(messages):
        if msg["role"] == "assistant":
            # Extract text content from message parts
            content_parts = msg.get("content", [])
            text = "\n".join(extract_text(part) for part in content_parts if part["type"] == "text")
            # Parse bullet list
            tasks = [line.strip('-• ').strip() for line in text.split('\n') if line.strip('-• ').strip()]
            return tasks
    return ["No assistant response found."]

if __name__ == '__main__':
    app.run(debug=True) 