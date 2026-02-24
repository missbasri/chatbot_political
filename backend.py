from flask import Flask, request, jsonify
from openai import OpenAI
import json
import csv
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load configuration at startup
with open(os.path.join(BASE_DIR, "config.json"), "r", encoding="utf-8") as f:
    config = json.load(f)

client = OpenAI(api_key=config["api_key"], base_url=config.get("base_url"))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message")
    history = data.get("history", [])
    
    p_id = data.get("participant_id", "UnknownID")
    p_topic = data.get("participant_topic", "UnknownTopic")

    # 1. Dynamically select the prompt file based on the topic
    prompt_filename = f"system_prompt_{p_topic}.md"
    prompt_path = os.path.join(BASE_DIR, prompt_filename)
    
    # 2. Try to read the specific markdown file
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        return jsonify({"error": f"Missing file: {prompt_filename} in the root folder."}), 400

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model=config["model"],
            messages=messages
        )
        reply = response.choices[0].message.content

        target_dir = os.path.join(BASE_DIR, "transcript", str(p_id), str(p_topic))
        os.makedirs(target_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        file_prefix = f"{p_id}_{p_topic}_{date_str}"
        
        md_path = os.path.join(target_dir, f"{file_prefix}.md")
        csv_path = os.path.join(target_dir, f"{file_prefix}.csv")

        # 3. Save the *specific* prompt used into the transcript folder
        if not os.path.exists(md_path):
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(system_prompt)

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerows([
                [ts, "User", user_input],
                [ts, "Bot", reply]
            ])

        return jsonify({"reply": reply})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)