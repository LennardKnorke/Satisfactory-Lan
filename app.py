from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory
import os, datetime
UPLOAD_FOLDER = 'files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt'}

done_tasks_file = "tasksdone.txt"
satisfactory_save_path = "C:/Users/Lennard/Downloads"

tasks = {
    "open" : [],
    "vitor" : [],
    "fritz" : [],
    "nico": [],
    "lennard": [],
    "fabsi": []
}
def get_latest_save():
    if not os.path.exists(satisfactory_save_path):
        return None
    saves = [f for f in os.listdir(satisfactory_save_path) if f.endswith(".sft")]
    if not saves:
        return None
    saves.sort(key=lambda f: os.path.getmtime(os.path.join(satisfactory_save_path, f)), reverse=True)
    return saves[0]


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "satisfactory_lan_secret"  # needed for flash messages

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_files():
    """
    Walks through UPLOAD_FOLDER and returns a nested list of files and folders.
    Only includes allowed file extensions.
    """
    file_tree = []

    for entry in sorted(os.listdir(app.config['UPLOAD_FOLDER'])):
        path = os.path.join(app.config['UPLOAD_FOLDER'], entry)

        if os.path.isfile(path) and allowed_file(entry):
            file_tree.append({
                "name": entry,
                "url": url_for("uploaded_file", filename=entry, _external=True),
                "children": []
            })

        elif os.path.isdir(path):
            children = []
            for sub in sorted(os.listdir(path)):
                if allowed_file(sub):
                    sub_url = url_for("uploaded_file_batch", folder=entry, filename=sub, _external=True)
                    children.append({"name": sub, "url": sub_url, "children": []})
            if children:
                file_tree.append({"name": entry, "url": None, "children": children})

    return file_tree


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        files = request.files.getlist("file")
        if not files or all(f.filename == "" for f in files):
            flash("No selected file(s)")
            return redirect(url_for("upload_file"))

        if len(files) > 1:
            # Create batch folder
            timestamp = datetime.datetime.now().strftime("batch_%Y%m%d_%H%M%S")
            batch_folder = os.path.join(app.config["UPLOAD_FOLDER"], timestamp)
            os.makedirs(batch_folder)

            urls = []
            for file in files:
                if file and allowed_file(file.filename):
                    filepath = os.path.join(batch_folder, file.filename)
                    file.save(filepath)
                    file_url = url_for(
                        "uploaded_file_batch",
                        folder=timestamp,
                        filename=file.filename,
                        _external=True,
                    )
                    urls.append(file_url)

            # Write urls.txt
            urls_path = os.path.join(batch_folder, "urls.txt")
            with open(urls_path, "w") as f:
                f.write("\n".join(urls))

            urls_url = url_for(
                "uploaded_file_batch",
                folder=timestamp,
                filename="urls.txt",
                _external=True,
            )
            flash(f"Uploaded {len(urls)} images in folder {timestamp}. URLs saved at: {urls_url}")

        else:
            file = files[0]
            if file and allowed_file(file.filename):
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(filepath)
                file_url = url_for("uploaded_file", filename=file.filename, _external=True)
                flash(f"Uploaded! Access it at: {file_url}")

        return redirect(url_for("upload_file"))  # ✅ Redirect after upload

    return render_template("index.html", file_tree=get_files(), tasks=tasks)
    

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/uploads/<folder>/<filename>")
def uploaded_file_batch(folder, filename):
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], folder), filename)



@app.route("/add_task", methods=["POST"])
def add_task():
    desc = request.form.get("task_desc")
    if desc:
        tasks["open"].append(desc)
        flash(f"Task added: {desc}")
    return redirect(url_for("upload_file"))


@app.route("/reserve_task/<user>", methods=["POST"])
def reserve_task(user):
    task = request.form.get("task")
    if task and task not in tasks[user]:
        tasks[user].append(task)
        flash(f"{user.capitalize()} reserved task: {task}")
    return redirect(url_for("upload_file"))


@app.route("/free_task/<user>", methods=["POST"])
def free_task(user):
    task = request.form.get("task")
    if task in tasks[user]:
        tasks[user].remove(task)
        flash(f"{user.capitalize()} freed task: {task}")
    return redirect(url_for("upload_file"))


@app.route("/delete_task", methods=["POST"])
def delete_task():
    task = request.form.get("task")
    if task in tasks["open"]:
        tasks["open"].remove(task)
        flash(f"Task deleted: {task}")
    return redirect(url_for("upload_file"))

@app.route("/complete_task/<user>", methods=["POST"])
def complete_task(user):
    task = request.form.get("task")
    if task not in tasks[user]:
        return redirect(url_for("upload_file"))

    # Find all users who reserved this task
    participants = [u.capitalize() for u, tlist in tasks.items() if u != "open" and task in tlist]

    # Remove task from *all* lists (users + open list)
    for u in tasks:
        if task in tasks[u]:
            tasks[u].remove(task)

    # Log to file
    with open(done_tasks_file, "a") as f:
        f.write(f"{datetime.datetime.now()} - {task} | Participants: {', '.join(participants)}\n")

    flash(f"Task '{task}' completed by {', '.join(participants)}!")
    return redirect(url_for("upload_file"))


@app.route("/download_latest_save")
def download_latest_save():
    latest = get_latest_save()
    if latest:
        return send_from_directory(satisfactory_save_path, latest, as_attachment=True)
    else:
        flash("No save file found!")
        return redirect(url_for("upload_file"))
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
